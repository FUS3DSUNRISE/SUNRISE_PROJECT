system_msg = (
                "You are an expert Blender 5.1 Python scripting assistant and 3D modeling engineer. "
                "Your sole output is executable Python code using the `bpy` module — nothing else. "
                "No markdown, no triple backticks, no prose, no comments, no explanations. "
                "The first line of your response must always be `import bpy`. "


                "\n\n═══ MANDATORY CODE STRUCTURE ═══"
                "\n1. import bpy and import math"
                "\n2. Define helper functions"
                "\n3. Clear the scene"
                "\n4. Build parts bottom to top"
                "\n5. Parent all parts to a root Empty"


                "\n\n═══ HELPER FUNCTIONS — ALWAYS DEFINE THESE EXACTLY ═══"


                "\n\ndef make_box(name, w, d, h, x, y, z):"
                "\n    verts = [(-w/2,-d/2,0),(w/2,-d/2,0),(w/2,d/2,0),(-w/2,d/2,0),"
                "\n             (-w/2,-d/2,h),(w/2,-d/2,h),(w/2,d/2,h),(-w/2,d/2,h)]"
                "\n    faces = [(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]"
                "\n    mesh = bpy.data.meshes.new(name)"
                "\n    mesh.from_pydata(verts, [], faces)"
                "\n    mesh.update()"
                "\n    obj = bpy.data.objects.new(name, mesh)"
                "\n    bpy.context.collection.objects.link(obj)"
                "\n    obj.location = (x, y, z)"
                "\n    return obj"


                "\n\ndef make_cylinder(name, r, h, x, y, z, segs=32):"
                "\n    verts, faces = [], []"
                "\n    for i in range(segs):"
                "\n        a = 2*math.pi*i/segs"
                "\n        verts += [(r*math.cos(a),r*math.sin(a),0),(r*math.cos(a),r*math.sin(a),h)]"
                "\n    for i in range(segs):"
                "\n        a,b = 2*i, 2*((i+1)%segs)"
                "\n        faces.append((a,b,b+1,a+1))"
                "\n    faces.append([2*i for i in range(segs-1,-1,-1)])"
                "\n    faces.append([2*i+1 for i in range(segs)])"
                "\n    mesh = bpy.data.meshes.new(name)"
                "\n    mesh.from_pydata(verts, [], faces)"
                "\n    mesh.update()"
                "\n    obj = bpy.data.objects.new(name, mesh)"
                "\n    bpy.context.collection.objects.link(obj)"
                "\n    obj.location = (x, y, z)"
                "\n    return obj"


                "\n\ndef set_material(obj, name, r, g, b, roughness=0.5, metallic=0.0):"
                "\n    mat = bpy.data.materials.new(name)"
                "\n    mat.use_nodes = True"
                "\n    bsdf = mat.node_tree.nodes['Principled BSDF']"
                "\n    bsdf.inputs['Base Color'].default_value = (r,g,b,1)"
                "\n    bsdf.inputs['Roughness'].default_value = roughness"
                "\n    bsdf.inputs['Metallic'].default_value = metallic"
                "\n    if obj.data.materials: obj.data.materials[0] = mat"
                "\n    else: obj.data.materials.append(mat)"


                "\n\ndef parent_objects(children, root_name):"
                "\n    root = bpy.data.objects.new(root_name, None)"
                "\n    bpy.context.collection.objects.link(root)"
                "\n    for obj in children: obj.parent = root"
                "\n    return root"


                "\n\n═══ SCENE CLEAR ═══"
                "\nbpy.ops.object.select_all(action='SELECT')"
                "\nbpy.ops.object.delete(use_global=False)"
                "\nfor block in bpy.data.meshes: bpy.data.meshes.remove(block)"
                "\nfor block in bpy.data.materials: bpy.data.materials.remove(block)"


                "\n\n═══ GEOMETRY RULES ═══"
                "\n- Every solid part must be a closed 3D volume. Never use flat quads."
                "\n- Never use obj.scale — put real dimensions into helper arguments."
                "\n- No floating parts. Every part must touch what it connects to."
                "\n- No part may extend beyond the boundary of the surface it sits on."
                "\n- Supporting elements (legs, feet, columns) must be inset by their own half-width:"
                "\n  leg_x = ±(surface_w/2 - leg_w/2), leg_y = ±(surface_d/2 - leg_d/2)"
                "\n- Stack parts correctly: part B on top of part A → B's Z = A's Z + A's height."
                "\n- Rear-attached parts (backrests, headboards): Y = -parent_depth/2 + part_depth/2"
                "\n- All dimensions in real-world meters."


                "\n\n═══ REFERENCE DIMENSIONS ═══"
                "\nFURNITURE:"
                "\n- Dining chair:  seat 0.45x0.45x0.04 @ Z=0.45 | legs 0.04x0.04x0.45 inset | back 0.45x0.05x0.50 @ rear"
                "\n- Armchair:      seat 0.65x0.70x0.08 @ Z=0.42 | arms 0.08x0.55x0.20 | back 0.65x0.08x0.55"
                "\n- Bar stool:     seat 0.35x0.35x0.04 @ Z=0.75 | legs 0.03x0.03x0.75"
                "\n- Dining table:  top 1.80x0.90x0.04 @ Z=0.75 | legs 0.06x0.06x0.75 inset"
                "\n- Coffee table:  top 1.20x0.60x0.04 @ Z=0.40 | legs 0.05x0.05x0.40"
                "\n- Desk:          top 1.40x0.70x0.03 @ Z=0.75 | legs 0.05x0.05x0.75 inset"
                "\n- Bookshelf:     body 0.80x0.30x1.80 | shelves 0.76x0.28x0.02 every 0.30m"
                "\n- Sofa (3-seat): base 2.10x0.90x0.20 | seat 2.10x0.75x0.15 | back 2.10x0.15x0.65 | arms 0.15x0.90x0.65"
                "\n- Bed (double):  frame 1.60x2.10x0.30 | mattress 1.54x2.04x0.20 | headboard 1.60x0.12x0.60"
                "\n- Wardrobe:      body 1.20x0.60x2.00 | doors 0.58x0.02x1.90"


                "\nARCHITECTURE:"
                "\n- Door: 0.90x0.05x2.10 | Window: 1.20x0.05x1.20 @ Z=0.90"
                "\n- Interior wall: length x 0.15 x 2.70 | Exterior wall: length x 0.30 x 2.70"
                "\n- Stair step: 0.90x0.28x0.18 | Room: ~5.0x4.0x2.70"


                "\nELECTRONICS:"
                "\n- Monitor (27in): screen 0.61x0.05x0.37 | base 0.30x0.25x0.03 | neck 0.04x0.04x0.35"
                "\n- Laptop: base 0.35x0.24x0.02 | screen 0.33x0.01x0.21"
                "\n- Smartphone: 0.075x0.008x0.160 | TV (55in): 1.22x0.04x0.71"


                "\nVEHICLES:"
                "\n- Car: body 4.50x1.80x0.70 @ Z=0.35 | roof 3.00x1.75x0.40 @ Z=1.05 | wheels r=0.32 h=0.22"
                "\n- Truck: cab 2.20x2.00x2.00 | trailer 8.00x2.40x2.70"


                "\nHUMAN BODY:"
                "\n- Head: sphere r=0.11 @ Z=1.62 | Neck: cyl r=0.05 h=0.08 @ Z=1.54"
                "\n- Torso: 0.44x0.22x0.56 @ Z=0.98 | Pelvis: 0.36x0.22x0.18 @ Z=0.80"
                "\n- Upper arm: cyl r=0.045 h=0.28 | Forearm: cyl r=0.035 h=0.25 | Hand: 0.09x0.04x0.10"
                "\n- Upper leg: cyl r=0.07 h=0.42 | Lower leg: cyl r=0.05 h=0.38 | Foot: 0.10x0.26x0.07"


                "\nKITCHEN:"
                "\n- Counter: 0.60x0.60x0.90 | Fridge: 0.70x0.70x1.80 | Oven: 0.60x0.60x0.85"
                "\n- Mug: cyl r=0.04 h=0.10 | Plate: cyl r=0.13 h=0.02 | Bottle: cyl r=0.04 h=0.28"


                "\n\n═══ MATERIALS ═══"
                "\n- Assign a material to every part. Default to wood if unspecified."
                "\n- Wood:     set_material(obj, 'Wood', 0.55, 0.35, 0.15, roughness=0.8)"
                "\n- Metal:    set_material(obj, 'Metal', 0.7, 0.7, 0.7, roughness=0.3, metallic=1.0)"
                "\n- Plastic:  set_material(obj, 'Plastic', 0.2, 0.2, 0.8, roughness=0.5)"
                "\n- Fabric:   set_material(obj, 'Fabric', 0.4, 0.3, 0.5, roughness=1.0)"
                "\n- Glass:    set_material(obj, 'Glass', 0.8, 0.9, 1.0, roughness=0.0)"
                "\n- Rubber:   set_material(obj, 'Rubber', 0.05, 0.05, 0.05, roughness=0.9)"
                "\n- Concrete: set_material(obj, 'Concrete', 0.5, 0.5, 0.5, roughness=0.95)"
                "\n- Skin:     set_material(obj, 'Skin', 0.87, 0.68, 0.54, roughness=0.7)"

                "\n\n═══ BLENDER API SAFETY RULES ═══"
                "\n- Never assign to obj.type or any object's .type attribute."
                "\n- To create a light, use bpy.data.lights.new(...) and then bpy.data.objects.new(..., light_data)."
                "\n- Never write code like light1.type = 'LIGHT'."
                "\n- Only use valid Blender Python API properties."
                "\n- The script must run without errors from top to bottom."
                "\n- Do not add cameras, lights, render settings, or scene styling unless explicitly required."
                "\n- Focus on geometry, materials, parenting, and mandatory GLB export only."
                "\n- Never use bpy.context.scene.render.resolution"
                "\n- If render resolution is needed, use resolution_x and resolution_y only"

                "\n\n═══ EXPORT RULES — MANDATORY ═══"
                "\n- The VERY LAST line of the code must ALWAYS be exactly:"
                "\nbpy.ops.export_scene.gltf(filepath='static/models/result.glb', export_format='GLB')"
)


import os
import subprocess
import logging
import traceback
import time
import shutil       
import platform
from dotenv import load_dotenv
from worker import celery
from app.extensions import db
from app.models.prompt import PromptRequest, PromptStatus
from langchain_openai import ChatOpenAI
from app.services.prompt_service import Parameters, PromptService, build_llm_prompt
import config

load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("tasks.process_prompt")

def get_blender_executable():
    # 1. Check in .env file
    env_blender = os.getenv("BLENDER_PATH")
    if env_blender and os.path.exists(env_blender):
        return env_blender
        
    # 2. Check system environment variables (PATH)
    path_blender = shutil.which("blender")
    if path_blender:
        return path_blender
        
    # 3. Check standard Windows and Steam installation paths
    if platform.system() == "Windows":
        drives = ["C:\\", "D:\\"]
        folders = [
            r"Program Files\Blender Foundation",
            r"Program Files (x86)\Steam\steamapps\common\Blender"
        ]
        for drive in drives:
            for folder in folders:
                search_path = os.path.join(drive, folder)
                if os.path.exists(search_path):
                    for root, dirs, files in os.walk(search_path):
                        if "blender.exe" in files:
                            return os.path.join(root, "blender.exe")
                            
    # 4. Check standard macOS path
    elif platform.system() == "Darwin":
        mac_path = "/Applications/Blender.app/Contents/MacOS/Blender"
        if os.path.exists(mac_path):
            return mac_path
            
    return None


class ConfigurationError(Exception):
    """Missing or invalid environment / config values."""


class LLMError(Exception):
    """Failure during LLM invocation."""


class BlenderError(Exception):
    def __init__(self, message, stderr="", returncode=None):
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


def _resolve_config(attr: str, fallback: str) -> str:
    return (
        getattr(config, attr, None)
        or getattr(getattr(config, "Config", object()), attr, None)
        or fallback
    )


def _write_script(prompt_id: int, code: str) -> str:
    filename = f"temp_script_{prompt_id}.py"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)
        logger.debug("Script written to %s (%d bytes)", filename, len(code))
    except OSError as exc:
        raise OSError(f"Could not write temp script '{filename}': {exc}") from exc
    return filename


def _cleanup(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
            logger.debug("Cleaned up temp file: %s", path)
    except OSError as exc:
        logger.warning("Could not remove temp file '%s': %s", path, exc)


def _fail_prompt(prompt: PromptRequest, message: str) -> None:
    prompt.status = PromptStatus.FAILED
    prompt.error_message = message[:2000]  # guard against oversized DB writes
    db.session.commit()


def _strip_code_fences(content: str) -> str:
    return content.replace("```python", "").replace("```", "").strip()


def _prepare_generated_code(code: str, output_path: str) -> str:
    export_line = f"bpy.ops.export_scene.gltf(filepath='{output_path}', export_format='GLB')"
    legacy_export_line = "bpy.ops.export_scene.gltf(filepath='static/models/result.glb', export_format='GLB')"

    code = code.strip()
    if legacy_export_line in code:
        return code.replace(legacy_export_line, export_line)
    if export_line in code:
        return code
    return f"{code}\n\n{export_line}"


def _build_generation_prompt(prompt: PromptRequest, parameters: dict) -> str:
    category = parameters.get("category") or getattr(prompt, "category", "Simple Objects")
    final_user_prompt = PromptService.create_final_prompt(
        user_query=prompt.prompt_text,
        category=category,
        parameters=parameters,
    )

    if not parameters:
        return final_user_prompt

    try:
        validated_params = Parameters(**parameters)
    except Exception as exc:
        logger.warning("Parameter validation failed in task for prompt_id=%s: %s", prompt.id, exc)
        return final_user_prompt

    return build_llm_prompt(final_user_prompt, validated_params)

@celery.task(
    bind=True,
    max_retries=2,
    default_retry_delay=10,
)

def process_prompt_task(self, prompt_id: int, parameters=None, fast_track_id=None):
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
            "Task started | prompt_id=%s status=%s fast_track_id=%s",
            prompt_id,
            prompt.status,
            fast_track_id,
        )

        try:
            prompt.status = PromptStatus.PROCESSING
            db.session.commit()

            base_url = _resolve_config("LLM_BASE_URL", "https://api.groq.com/openai/v1")
            model_name = _resolve_config("LLM_MODEL", "llama-3.3-70b-versatile")
            api_key = _resolve_config("LLM_API_KEY", "")

            if not api_key:
                raise ConfigurationError("LLM_API_KEY is empty - set it in .env or config.")

            logger.info(
                "LLM config | base_url=%s model=%s prompt_id=%s",
                base_url,
                model_name,
                prompt_id,
            )
            llm = ChatOpenAI(base_url=base_url, api_key=api_key, model=model_name)

            if fast_track_id:

                source = PromptRequest.query.get(fast_track_id)
                if not source or not source.generated_code:
                    raise LLMError("Source for fast-track not found or has no code.")

                logger.info("Fast-track mode: revising existing code from ID=%s", fast_track_id)

                generation_prompt = _build_generation_prompt(prompt, parameters)

                modification_command = prompt.modification_command or ""

                human_prompt = (
                    "Revise the existing Blender Python script below.\n"
                    "You must update the model based on BOTH the updated parameters AND the modification command.\n\n"
                    "If there is any conflict, the parameters must be strictly respected.\n\n"

                    f"MODIFICATION COMMAND:\n{modification_command}\n\n"

                    f"UPDATED REQUEST (parameters):\n{generation_prompt}\n\n"

                    "EXISTING SCRIPT:\n"
                    f"{source.generated_code}"
            )
                
            else:
                human_prompt = _build_generation_prompt(prompt, parameters)

            t0 = time.perf_counter()
            try:
                response = llm.invoke([
                    ("system", system_msg),
                    ("human", human_prompt),
                ])
            except Exception as exc:
                raise LLMError(f"LLM call failed: {exc}") from exc

            elapsed_llm = time.perf_counter() - t0
            logger.info(
                "LLM response received | prompt_id=%s elapsed=%.2fs tokens~%d",
                prompt_id,
                elapsed_llm,
                len(response.content) // 4,
            )

            generated_code = _strip_code_fences(response.content)
            if "import bpy" not in generated_code:
                raise LLMError("Generated code does not contain 'import bpy' - likely malformed.")

            output_filename = f"prompt_{prompt_id}.glb"
            output_path = f"static/models/{output_filename}"
            generated_code = _prepare_generated_code(generated_code, output_path)

            logger.debug("Generated code preview (first 300 chars):\n%s", generated_code[:300])

            prompt.generated_code = generated_code
            prompt.error_message = None
            db.session.commit()

            script_filename = _write_script(prompt_id, generated_code)

            blender_path = get_blender_executable()
            if not blender_path:
                raise ConfigurationError(
                    "Blender executable not found automatically! Please set BLENDER_PATH in your .env file."
                )

            logger.info("Launching Blender | prompt_id=%s script=%s", prompt_id, script_filename)
            t1 = time.perf_counter()

            result = subprocess.run(
                [blender_path, "--background", "--python", script_filename],
                capture_output=True,
                text=True,
                timeout=120,
            )

            elapsed_blender = time.perf_counter() - t1
            logger.info(
                "Blender finished | prompt_id=%s returncode=%d elapsed=%.2fs",
                prompt_id,
                result.returncode,
                elapsed_blender,
            )

            if result.returncode != 0:
                logger.error(
                    "Blender stderr (prompt_id=%s):\n%s",
                    prompt_id,
                    result.stderr[-3000:],
                )
                raise BlenderError(
                    "Blender exited with non-zero return code.",
                    stderr=result.stderr,
                    returncode=result.returncode,
                )

            if result.stderr:
                logger.warning(
                    "Blender stderr (non-fatal, prompt_id=%s):\n%s",
                    prompt_id,
                    result.stderr[-1000:],
                )

            if not os.path.exists(output_path):
                raise BlenderError(
                    f"Blender ran successfully but output file was not created: {output_path}",
                    stderr=result.stderr,
                )

            glb_size = os.path.getsize(output_path)
            logger.info(
                "GLB created | prompt_id=%s path=%s size=%d bytes",
                prompt_id,
                output_path,
                glb_size,
            )

            prompt.status = PromptStatus.COMPLETED
            prompt.result_path = f"/static/models/{output_filename}"
            db.session.commit()
            logger.info("Task completed | prompt_id=%s result_path=%s", prompt_id, prompt.result_path)

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

        except BlenderError as exc:
            logger.error(
                "Blender error | prompt_id=%s returncode=%s: %s\nstderr tail:\n%s",
                prompt_id,
                exc.returncode,
                exc,
                exc.stderr[-2000:],
            )
            _fail_prompt(prompt, str(exc))

        except subprocess.TimeoutExpired:
            msg = "Blender process timed out after 120 seconds."
            logger.error("%s | prompt_id=%s", msg, prompt_id)
            _fail_prompt(prompt, msg)

        except Exception as exc:
            tb = traceback.format_exc()
            logger.error("Unexpected error | prompt_id=%s:\n%s", prompt_id, tb)
            _fail_prompt(prompt, f"Unexpected error: {exc}")
            try:
                raise self.retry(exc=exc)
            except self.MaxRetriesExceededError:
                logger.error("Max retries exceeded | prompt_id=%s", prompt_id)

        finally:
            _cleanup(script_filename)
