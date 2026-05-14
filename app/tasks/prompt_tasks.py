from app.services.blender.blender_executor import (
    write_script,
    cleanup_file,
    run_blender_script,
    BlenderExecutionError,
)

import os
import ast
import logging
import traceback
import time
import textwrap
from dotenv import load_dotenv

from worker import celery
from app.extensions import db
from app.models.prompt import PromptRequest, PromptStatus
from app.models.imported_asset import ImportedAsset
from app.services.llm.llm_service import LLMService
from app.services.prompt_service import Parameters, PromptService, build_llm_prompt

import config


load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("tasks.process_prompt")


class ConfigurationError(Exception):
    """Missing or invalid environment / config values."""


class LLMError(Exception):
    """Failure during LLM invocation."""


def _resolve_config(attr: str, fallback: str) -> str:
    return (
        getattr(config, attr, None)
        or getattr(getattr(config, "Config", object()), attr, None)
        or fallback
    )


def load_system_prompt() -> str:
    prompt_path = _resolve_config(
        "LLM_SYSTEM_PROMPT_PATH",
        "app/prompts/system_prompt.txt"
    )

    if not os.path.exists(prompt_path):
        raise ConfigurationError(f"System prompt file not found: {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read().strip()


def _fail_prompt(prompt: PromptRequest, message: str) -> None:
    prompt.status = PromptStatus.FAILED
    prompt.error_message = message[:2000]
    db.session.commit()


def _strip_code_fences(content: str) -> str:
    return content.replace("```python", "").replace("```", "").strip()


def _prepare_generated_code(code: str, output_path: str) -> str:
    export_line = f"bpy.ops.export_scene.gltf(filepath='{output_path}', export_format='GLB')"
    legacy_export_line = "bpy.ops.export_scene.gltf(filepath='static/models/result.glb', export_format='GLB')"

    code = code.strip()

    if legacy_export_line in code:
        code = code.replace(legacy_export_line, export_line)
    elif export_line not in code:
        code = f"{code}\n\n{export_line}"
        
    base_header = """
    import bpy
    import math
    import bmesh

    # Clear the default Blender scene (removes the default Cube, Light, and Camera)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    def make_box(name, w, d, h, x, y, z):
        verts = [(-w/2,-d/2,0),(w/2,-d/2,0),(w/2,d/2,0),(-w/2,d/2,0),
                 (-w/2,-d/2,h),(w/2,-d/2,h),(w/2,d/2,h),(-w/2,d/2,h)]
        faces = [(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        obj.location = (x, y, z)
        return obj

    def make_cylinder(name, r, h, x, y, z, segs=32):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r, radius2=r, depth=h)
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        obj.location = (x, y, z)
        return obj

    def make_sphere(name, r, x, y, z, segments=32, rings=16):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=r)
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        obj.location = (x, y, z)
        return obj

    def set_material(name, r, g, b, roughness=0.5, metallic=0.0):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        if 'Principled BSDF' in mat.node_tree.nodes:
            bsdf = mat.node_tree.nodes['Principled BSDF']
            bsdf.inputs['Base Color'].default_value = (r, g, b, 1)
            bsdf.inputs['Roughness'].default_value = roughness
            bsdf.inputs['Metallic'].default_value = metallic
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and not obj.data.materials:
                obj.data.materials.append(mat)
                
    def build_chair(w, d, h):
        seat_h = h * 0.45; thick = 0.05; leg_w = 0.05
        make_box("Seat", w, d, thick, 0, 0, seat_h)
        make_box("Leg1", leg_w, leg_w, seat_h, w/2-leg_w/2, d/2-leg_w/2, 0)
        make_box("Leg2", leg_w, leg_w, seat_h, -w/2+leg_w/2, d/2-leg_w/2, 0)
        make_box("Leg3", leg_w, leg_w, seat_h, w/2-leg_w/2, -d/2+leg_w/2, 0)
        make_box("Leg4", leg_w, leg_w, seat_h, -w/2+leg_w/2, -d/2+leg_w/2, 0)
        make_box("Back", w, thick, h-seat_h, 0, -d/2+thick/2, seat_h+thick)
    """
    
    # Strip leading whitespace so the Python syntax works perfectly
    base_header = textwrap.dedent(base_header).strip()

    return f"{base_header}\n\n{code}"


def _build_generation_prompt(prompt: PromptRequest, parameters: dict) -> str:
    final_user_prompt = PromptService.create_final_prompt(
        user_query=prompt.prompt_text,
        parameters=parameters,
    )

    if not parameters:
        return final_user_prompt

    try:
        validated_params = Parameters(**parameters)
    except Exception as exc:
        logger.warning(
            "Parameter validation failed in task for prompt_id=%s: %s",
            prompt.id,
            exc
        )
        return final_user_prompt

    return build_llm_prompt(final_user_prompt, validated_params)


def _build_imported_asset_modification_prompt(
    app,
    prompt: PromptRequest,
    imported_asset_id: int
) -> str:
    imported_asset = ImportedAsset.query.get(imported_asset_id)

    if not imported_asset:
        raise LLMError("Imported asset not found.")

    input_asset_path = os.path.abspath(
        os.path.join(app.root_path, "..", imported_asset.file_path)
    )

    if not os.path.exists(input_asset_path):
        raise LLMError(f"Imported asset file not found: {input_asset_path}")

    modification_command = prompt.modification_command or ""

    return (
        "Modify the existing imported 3D asset using Blender Python.\n"
        "Do NOT create a new object from scratch.\n"
        "You must import the existing asset first, then apply the requested modification.\n\n"

        f"IMPORTED ASSET FILE PATH:\n{input_asset_path}\n\n"

        f"ASSET METADATA:\n{imported_asset.metadata_json}\n\n"

        f"MODIFICATION COMMAND:\n{modification_command}\n\n"

        "Required behavior:\n"
        "- Import the existing asset from the file path above.\n"
        "- Keep the imported asset structure.\n"
        "- Modify only existing mesh objects when changing geometry or materials.\n"
        "- Do not apply materials to lights, cameras, empties or non-mesh objects.\n"
        "- When iterating over objects, always check: if obj.type == 'MESH'.\n"
        "- Before accessing obj.data.materials, always check that obj.type == 'MESH'.\n"
        "- Ignore objects of type LIGHT, CAMERA, EMPTY, ARMATURE or other non-mesh types.\n"
        "- If changing material, create or reuse a material and assign it only to mesh objects.\n"
        "- Do not delete the whole imported asset unless the command explicitly asks for it.\n"
        "- Export the final result as GLB using the mandatory export line.\n\n"

        "Blender import instructions:\n"
        "- For .glb or .gltf files, use bpy.ops.import_scene.gltf(filepath=...).\n"
        "- For .obj files, use bpy.ops.wm.obj_import(filepath=...) if available.\n"
        "- After import, get imported objects from bpy.context.selected_objects or bpy.data.objects.\n\n"

        "Safe material modification pattern:\n"
        "for obj in bpy.data.objects:\n"
        "    if obj.type == 'MESH':\n"
        "        # safe to access obj.data.materials here\n"
        "        pass\n\n"

        "Your output must be executable Python code only."
    )

def _build_fast_track_prompt(prompt: PromptRequest, parameters: dict, fast_track_id: int) -> str:
    source = PromptRequest.query.get(fast_track_id)

    if not source or not source.generated_code:
        raise LLMError("Source for fast-track not found or has no code.")

    logger.info("Fast-track mode: revising existing code from ID=%s", fast_track_id)

    generation_prompt = _build_generation_prompt(prompt, parameters)
    modification_command = prompt.modification_command or ""

    return (
        "Revise the existing Blender Python script below.\n"
        "You must update the model based on BOTH the updated parameters AND the modification command.\n\n"
        "CRITICAL: Keep the code extremely concise. DO NOT define `make_box` or other helper functions, they are pre-loaded.\n\n"
        "If there is any conflict, the parameters must be strictly respected.\n\n"

        f"MODIFICATION COMMAND:\n{modification_command}\n\n"

        f"UPDATED REQUEST / PARAMETERS:\n{generation_prompt}\n\n"

        "EXISTING SCRIPT:\n"
        f"{source.generated_code}"
    )


@celery.task(
    bind=True,
    max_retries=2,
    default_retry_delay=10,
)
def process_prompt_task(
    self,
    prompt_id: int,
    parameters=None,
    fast_track_id=None,
    imported_asset_id=None
):
    from app import create_app

    app = create_app()

    with app.app_context():
        script_filename = None
        prompt = PromptRequest.query.get(prompt_id)

        if not prompt:
            logger.error("Prompt ID %s not found in database - aborting.", prompt_id)
            return

        if parameters is None:
            parameters = prompt.parameters or {}

        logger.info(
            "Prompt loaded | prompt_id=%s user_id=%s status=%s has_parameters=%s fast_track=%s imported_asset=%s",
            prompt_id,
            prompt.user_id,
            prompt.status.value,
            bool(parameters),
            bool(fast_track_id),
            bool(imported_asset_id),
        )

        logger.info(
            "Task started | prompt_id=%s status=%s fast_track_id=%s imported_asset_id=%s",
            prompt_id,
            prompt.status.value,
            fast_track_id,
            imported_asset_id,
        )

        try:
            prompt.status = PromptStatus.PROCESSING
            db.session.commit()

            llm_service = LLMService()

            logger.info(
                "LLM config | prompt_id=%s config=%s",
                prompt_id,
                llm_service.get_config_summary(),
            )

            if imported_asset_id:
                generation_mode = "imported_asset_modification"
                human_prompt = _build_imported_asset_modification_prompt(
                    app=app,
                    prompt=prompt,
                    imported_asset_id=imported_asset_id
                )

            elif fast_track_id:
                generation_mode = "fast_track_modification"
                human_prompt = _build_fast_track_prompt(
                    prompt=prompt,
                    parameters=parameters,
                    fast_track_id=fast_track_id
                )

            else:
                generation_mode = "creation"
                human_prompt = _build_generation_prompt(prompt, parameters)

            logger.info("LLM input prepared | prompt_id=%s", prompt_id)

            logger.info(
                "Generation mode | prompt_id=%s mode=%s parameters=%s",
                prompt_id,
                generation_mode,
                parameters,
            )

            logger.info(
                "LLM human prompt preview | prompt_id=%s preview=%s",
                prompt_id,
                human_prompt[:500],
            )

            t0 = time.perf_counter()

            try:
                system_msg = load_system_prompt()

                logger.info(
                    "LLM system prompt loaded | prompt_id=%s length=%d",
                    prompt_id,
                    len(system_msg),
                )

                llm_output = llm_service.generate(system_msg, human_prompt)

            except Exception as exc:
                raise LLMError(f"LLM call failed: {exc}") from exc

            elapsed_llm = time.perf_counter() - t0

            logger.info(
                "LLM response received | prompt_id=%s elapsed=%.2fs tokens~%d",
                prompt_id,
                elapsed_llm,
                len(llm_output) // 4,
            )

            logger.info(
                "LLM output preview | prompt_id=%s preview=%s",
                prompt_id,
                llm_output[:500],
            )

            generated_code = _strip_code_fences(llm_output)

            logger.info(
                "Generated code validation | prompt_id=%s code_length=%d",
                prompt_id,
                len(generated_code),
            )

            if len(generated_code) < 10:
                raise LLMError("Generated code is too short - likely malformed.")

            output_filename = f"prompt_{prompt_id}.glb"
            output_path = f"static/models/{output_filename}"

            generated_code = _prepare_generated_code(generated_code, output_path)

            try:
                ast.parse(generated_code)
            except SyntaxError as e:
                raise LLMError(f"Generated script has syntax errors (likely truncated by token limit): {e}")

            prompt.generated_code = generated_code
            prompt.error_message = None
            db.session.commit()

            script_filename = write_script(prompt_id, generated_code)

            logger.info(
                "Temporary script ready | prompt_id=%s output_path=%s",
                prompt_id,
                output_path,
            )

            run_blender_script(
                prompt_id=prompt_id,
                script_filename=script_filename,
                output_path=output_path,
                timeout=120,
            )

            prompt.status = PromptStatus.COMPLETED
            prompt.result_path = f"/static/models/{output_filename}"
            db.session.commit()

            logger.info(
                "Task completed | prompt_id=%s result_path=%s",
                prompt_id,
                prompt.result_path
            )

        except ConfigurationError as exc:
            logger.critical("Configuration error | prompt_id=%s: %s", prompt_id, exc)
            _fail_prompt(prompt, str(exc))

        except LLMError as exc:
            logger.error("LLM error | prompt_id=%s: %s", prompt_id, exc)
            _fail_prompt(prompt, str(exc))

            try:
                raise self.retry(exc=exc)
            except self.MaxRetriesExceededError:
                logger.error("Max retries exceeded for LLM | prompt_id=%s", prompt_id)

        except BlenderExecutionError as exc:
            logger.error(
                "Blender error | prompt_id=%s returncode=%s: %s\nstderr tail:\n%s",
                prompt_id,
                exc.returncode,
                exc,
                exc.stderr[-2000:],
            )
            _fail_prompt(prompt, str(exc))

        except Exception as exc:
            tb = traceback.format_exc()

            logger.error(
                "Unexpected error | prompt_id=%s:\n%s",
                prompt_id,
                tb
            )

            _fail_prompt(prompt, f"Unexpected error: {exc}")

            try:
                raise self.retry(exc=exc)
            except self.MaxRetriesExceededError:
                logger.error("Max retries exceeded | prompt_id=%s", prompt_id)

        finally:
            cleanup_file(script_filename)