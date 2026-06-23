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
import re
from pathlib import Path
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
    match = re.search(r"```(?:python)?\s*(.*?)```", content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
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
        bmesh.ops.translate(bm, vec=(0.0, 0.0, h/2), verts=bm.verts)
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

    def make_cone(name, r, h, x, y, z, segs=32):
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs, radius1=r, radius2=0, depth=h)
        bmesh.ops.translate(bm, vec=(0.0, 0.0, h/2), verts=bm.verts)
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.collection.objects.link(obj)
        obj.location = (x, y, z)
        return obj

    def make_torus(name, r_major, r_minor, x, y, z, major_segs=32, minor_segs=12):
        try:
            m_segs = max(3, int(major_segs))
            n_segs = max(3, int(minor_segs))
        except (ValueError, TypeError):
            m_segs, n_segs = 32, 12
            
        bpy.ops.mesh.primitive_torus_add(
            major_radius=r_major, 
            minor_radius=r_minor, 
            major_segments=m_segs, 
            minor_segments=n_segs, 
            location=(x, y, z)
        )
        obj = bpy.context.active_object
        obj.name = name
        if obj.data:
            obj.data.name = name
        return obj

    def set_material(name, r, g, b, roughness=0.5, metallic=0.0, target_obj_name=None):
        if isinstance(roughness, str):
            target_obj_name = roughness
            roughness = 0.5
            metallic = 0.0
        elif isinstance(metallic, str):
            target_obj_name = metallic
            metallic = 0.0
            
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        if 'Principled BSDF' in mat.node_tree.nodes:
            bsdf = mat.node_tree.nodes['Principled BSDF']
            bsdf.inputs['Base Color'].default_value = (r, g, b, 1)
            bsdf.inputs['Roughness'].default_value = float(roughness)
            bsdf.inputs['Metallic'].default_value = float(metallic)
            
        if target_obj_name and target_obj_name in bpy.data.objects:
            obj = bpy.data.objects[target_obj_name]
            if obj.type == 'MESH':
                obj.data.materials.clear()
                obj.data.materials.append(mat)
        else:
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

    def build_table(w, d, h):
        thick = 0.05
        leg_w = 0.08
        make_box("Top", w, d, thick, 0, 0, h-thick)
        make_box("Leg1", leg_w, leg_w, h-thick, w/2-leg_w, d/2-leg_w, 0)
        make_box("Leg2", leg_w, leg_w, h-thick, -w/2+leg_w, d/2-leg_w, 0)
        make_box("Leg3", leg_w, leg_w, h-thick, w/2-leg_w, -d/2+leg_w, 0)
        make_box("Leg4", leg_w, leg_w, h-thick, -w/2+leg_w, -d/2+leg_w, 0)

    def build_tree(w, d, h):
        trunk_h = h * 0.6
        trunk_r = w * 0.1
        foliage_r = w * 0.5
        make_cylinder("Trunk", trunk_r, trunk_h, 0, 0, 0)
        make_sphere("Foliage", foliage_r, 0, 0, trunk_h + foliage_r*0.2)

    def build_sofa(w, d, h):
        seat_h = h * 0.4
        arm_w = w * 0.15
        back_t = d * 0.2
        make_box("Seat", w - 2*arm_w, d - back_t, seat_h, 0, back_t/2, 0)
        make_box("Backrest", w, back_t, h, 0, -d/2 + back_t/2, 0)
        make_box("Armrest_L", arm_w, d, h * 0.6, -w/2 + arm_w/2, 0, 0)
        make_box("Armrest_R", arm_w, d, h * 0.6, w/2 - arm_w/2, 0, 0)

    def build_bed(w, d, h):
        frame_h = h * 0.3
        mattress_h = h * 0.2
        headboard_h = h
        head_t = 0.1
        make_box("Frame", w, d, frame_h, 0, 0, 0)
        make_box("Mattress", w - 0.1, d - head_t - 0.05, mattress_h, 0, -head_t/2, frame_h)
        make_box("Headboard", w, head_t, headboard_h, 0, d/2 - head_t/2, 0)

    def build_lamp(w, d, h):
        base_r = min(w, d) * 0.4
        base_h = h * 0.05
        pole_r = min(w, d) * 0.05
        pole_h = h * 0.7
        shade_r = min(w, d) * 0.5
        shade_h = h * 0.25
        make_cylinder("Base", base_r, base_h, 0, 0, 0)
        make_cylinder("Pole", pole_r, pole_h, 0, 0, base_h)
        make_cone("Shade", shade_r, shade_h, 0, 0, base_h + pole_h)

    def build_car(w, d, h):
        wheel_r = h * 0.2
        wheel_w = d * 0.2
        body_h = h * 0.4
        roof_h = h * 0.3
        make_box("Car_Body", w, d*0.8, body_h, 0, 0, wheel_r)
        make_box("Car_Roof", w*0.6, d*0.7, roof_h, -w*0.1, 0, wheel_r + body_h)
        for i, (x, y) in enumerate([(1, 1), (1, -1), (-1, 1), (-1, -1)]):
            wh = make_cylinder(f"Car_Wheel_{i}", wheel_r, wheel_w, w*0.3*x, d*0.4*y + wheel_w/2, wheel_r)
            wh.rotation_euler[0] = 1.5708

    def build_laptop(w, d, h):
        base_t = h * 0.05
        make_box("Laptop_Base", w, d, base_t, 0, 0, 0)
        make_box("Laptop_Keyboard", w * 0.8, d * 0.6, h * 0.02, 0, -d * 0.1, base_t)
        scr = make_box("Laptop_Screen", w, base_t, h*0.95, 0, d/2 - base_t/2, base_t)
        scr.rotation_euler[0] = -0.2618

    def build_wardrobe(w, d, h):
        make_box("Wardrobe_Body", w, d, h, 0, 0, 0)
        door_l = make_box("Wardrobe_Door_L", w*0.48, d*0.05, h*0.95, -w*0.49, -d/2 - d*0.025, h*0.025)
        for v in door_l.data.vertices: v.co.x += w*0.24
        door_r = make_box("Wardrobe_Door_R", w*0.48, d*0.05, h*0.95, w*0.49, -d/2 - d*0.025, h*0.025)
        for v in door_r.data.vertices: v.co.x -= w*0.24

    def build_cat(w, d, h):
        body_w, body_d, body_h = w*0.6, d*0.4, h*0.4
        make_box("Cat_Body", body_w, body_d, body_h, 0, 0, h*0.4)
        make_box("Cat_Head", w*0.25, d*0.3, h*0.3, w*0.4, 0, h*0.7)
        make_cone("Cat_Ear_L", w*0.1, h*0.2, w*0.4, d*0.1, h*1.0)
        make_cone("Cat_Ear_R", w*0.1, h*0.2, w*0.4, -d*0.1, h*1.0)
        tail = make_box("Cat_Tail", w*0.4, d*0.1, h*0.1, -w*0.4, 0, h*0.7)
        tail.rotation_euler[1] = -0.5236
        for i, (x, y) in enumerate([(0.2, 0.15), (0.2, -0.15), (-0.2, 0.15), (-0.2, -0.15)]):
            make_box(f"Cat_Leg_{i}", w*0.1, d*0.1, h*0.4, w*x, d*y, 0)

    def build_pallet(w, d, h):
        supp_w, supp_h = w*0.1, h*0.8
        for i, y in enumerate([-d*0.4, 0, d*0.4]):
            make_box(f"Pallet_Support_{i}", w, supp_w, supp_h, 0, y, 0)
        board_w, board_h = w*0.15, h*0.2
        for i, x in enumerate([-w*0.4, -w*0.2, 0, w*0.2, w*0.4]):
            make_box(f"Pallet_Board_{i}", board_w, d, board_h, x, 0, supp_h)

    def build_screw(w, d, h):
        shank_r = min(w, d) * 0.2
        shank_h = h * 0.7
        head_r = min(w, d) * 0.4
        head_h = h * 0.15
        tip_h = h * 0.15
        make_cylinder("Screw_Shank", shank_r, shank_h, 0, 0, tip_h)
        tip = make_cone("Screw_Tip", shank_r, tip_h, 0, 0, tip_h)
        tip.rotation_euler[1] = 3.14159
        make_cylinder("Screw_Head", head_r, head_h, 0, 0, tip_h + shank_h)
        for i in range(8):
            make_torus(f"Screw_Thread_{i}", shank_r, shank_r * 0.25, 0, 0, tip_h + (i / 7) * shank_h)
        make_box("Screw_Drive_1", head_r*1.4, head_r*0.2, head_h*0.1, 0, 0, h)
        make_box("Screw_Drive_2", head_r*0.2, head_r*1.4, head_h*0.1, 0, 0, h)
    """
    
    # Strip leading whitespace so the Python syntax works perfectly
    base_header = textwrap.dedent(base_header).strip()

    return f"{base_header}\n\n{code}"


def _write_temp_helper_script(prompt_id: int, prefix: str, code: str) -> str:
    if not isinstance(prompt_id, int) or prompt_id < 0:
        raise ValueError(f"Invalid prompt_id: {prompt_id!r}")

    tmp_dir = Path(os.getenv("BLENDER_SCRIPT_DIR", "/tmp/blender_scripts"))
    tmp_dir.mkdir(parents=True, exist_ok=True)

    filename = tmp_dir / f"{prefix}_{prompt_id}.py"
    filename.write_text(code, encoding="utf-8")
    filename.chmod(0o600)
    return str(filename)


def _get_root_prompt(prompt: PromptRequest) -> PromptRequest:
    current = prompt
    while current.parent_prompt is not None:
        current = current.parent_prompt
    return current


def _collect_prompt_versions(prompt: PromptRequest) -> list[PromptRequest]:
    versions: list[PromptRequest] = []

    def dfs(node: PromptRequest) -> None:
        versions.append(node)
        children = sorted(
            node.refined_versions,
            key=lambda item: item.created_at.timestamp() if item.created_at else 0
        )
        for child in children:
            dfs(child)

    dfs(_get_root_prompt(prompt))
    return versions


def _get_thumbnail_target(prompt: PromptRequest) -> tuple[PromptRequest, int]:
    root_prompt = _get_root_prompt(prompt)
    versions = _collect_prompt_versions(prompt)

    for index, item in enumerate(versions, start=1):
        if item.id == prompt.id:
            return root_prompt, index

    return root_prompt, len(versions) + 1


def _build_thumbnail_render_script(model_path: str, thumbnail_path: str) -> str:
    return textwrap.dedent(f"""
        import os
        import bpy
        from mathutils import Vector

        MODEL_PATH = {model_path!r}
        THUMBNAIL_PATH = {thumbnail_path!r}

        bpy.ops.wm.read_factory_settings(use_empty=True)

        extension = os.path.splitext(MODEL_PATH)[1].lower()
        if extension in (".glb", ".gltf"):
            bpy.ops.import_scene.gltf(filepath=MODEL_PATH)
        elif extension == ".obj":
            if hasattr(bpy.ops.wm, "obj_import"):
                bpy.ops.wm.obj_import(filepath=MODEL_PATH)
            else:
                bpy.ops.import_scene.obj(filepath=MODEL_PATH)
        else:
            raise RuntimeError("Unsupported thumbnail source: " + extension)

        scene = bpy.context.scene
        mesh_objects = [obj for obj in scene.objects if obj.type == "MESH"]
        if not mesh_objects:
            raise RuntimeError("No mesh objects available for thumbnail generation")

        bounds = []
        for obj in mesh_objects:
            for corner in obj.bound_box:
                bounds.append(obj.matrix_world @ Vector(corner))

        min_corner = Vector((
            min(point.x for point in bounds),
            min(point.y for point in bounds),
            min(point.z for point in bounds),
        ))
        max_corner = Vector((
            max(point.x for point in bounds),
            max(point.y for point in bounds),
            max(point.z for point in bounds),
        ))

        center = (min_corner + max_corner) / 2

        camera_data = bpy.data.cameras.new("ThumbnailCamera")
        camera = bpy.data.objects.new("ThumbnailCamera", camera_data)
        scene.collection.objects.link(camera)
        camera.location = center + Vector((6.8, -6.8, 4.6))
        camera.data.lens = 45
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.camera = camera

        key_light_data = bpy.data.lights.new(name="ThumbnailKeyLight", type="AREA")
        key_light_data.energy = 3000
        key_light = bpy.data.objects.new(name="ThumbnailKeyLight", object_data=key_light_data)
        scene.collection.objects.link(key_light)
        key_light.location = center + Vector((5.0, 4.2, 7.0))

        fill_light_data = bpy.data.lights.new(name="ThumbnailFillLight", type="AREA")
        fill_light_data.energy = 1200
        fill_light = bpy.data.objects.new(name="ThumbnailFillLight", object_data=fill_light_data)
        scene.collection.objects.link(fill_light)
        fill_light.location = center + Vector((-4.6, -3.0, 4.0))

        if scene.world is None:
            scene.world = bpy.data.worlds.new("ThumbnailWorld")
        scene.world.use_nodes = True
        background = scene.world.node_tree.nodes.get("Background")
        if background:
            background.inputs[0].default_value = (0.08, 0.08, 0.08, 1.0)
            background.inputs[1].default_value = 0.8

        scene.render.engine = "CYCLES"
        scene.cycles.samples = 8
        scene.render.resolution_x = 512
        scene.render.resolution_y = 512
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = False
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = THUMBNAIL_PATH

        bpy.ops.render.render(write_still=True)
    """).strip()


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

        "PLAN FIRST (CHAIN OF THOUGHT): Before calling any functions or writing logic, write a block of Python comments (starting with `#`) to act as your modification blueprint. Describe exactly which meshes or materials you plan to select and what transformations (scale, location, etc.) you will apply to satisfy the command.\n\n"

        "Required behavior:\n"
        "- Import the existing asset from the file path above.\n"
        "- Keep the imported asset structure.\n"
        "- Modify only existing mesh objects using transformations (e.g., obj.scale, obj.location, obj.rotation_euler) or material changes.\n"
        "- NEVER create new objects (do not use make_box, make_cylinder, make_cone, make_torus, etc.) unless explicitly commanded to ADD a new part.\n"
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

        "Your output must start with your Python comment blueprint, followed immediately by the executable Python code."
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
        "PLAN FIRST (CHAIN OF THOUGHT): Before writing any code, write a block of Python comments (starting with `#`) explaining what specific math/coordinate changes are needed to the existing script to satisfy the new parameters and command.\n\n"
        
        "CRITICAL: Keep the code extremely concise. DO NOT define `make_box` or other helper functions, they are pre-loaded.\n\n"
        "CRITICAL: To change the size, shape, or position of a part, you MUST modify the arguments of the EXISTING function calls (w, d, h, x, y, z)!\n"
        "Do NOT add new objects unless the command explicitly asks to ADD a new part.\n\n"
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

            thumbnail_script_filename = None
            root_prompt, version_index = _get_thumbnail_target(prompt)
            thumbnail_rel_path = f"/static/models/thumbnails/prompt_{root_prompt.id}/version_{version_index}.png"
            thumbnail_disk_path = os.path.abspath(
                os.path.join(
                    app.root_path,
                    "..",
                    "static",
                    "models",
                    "thumbnails",
                    f"prompt_{root_prompt.id}",
                    f"version_{version_index}.png",
                )
            )
            os.makedirs(os.path.dirname(thumbnail_disk_path), exist_ok=True)

            try:
                thumbnail_script = _build_thumbnail_render_script(
                    model_path=os.path.abspath(os.path.join(app.root_path, "..", output_path)),
                    thumbnail_path=thumbnail_disk_path,
                )
                thumbnail_script_filename = _write_temp_helper_script(
                    prompt_id=prompt_id,
                    prefix="thumbnail_script",
                    code=thumbnail_script,
                )

                run_blender_script(
                    prompt_id=prompt_id,
                    script_filename=thumbnail_script_filename,
                    output_path=thumbnail_disk_path,
                    timeout=120,
                )

                prompt.thumbnail_path = thumbnail_rel_path
                logger.info(
                    "Thumbnail rendered | prompt_id=%s thumbnail_path=%s",
                    prompt_id,
                    prompt.thumbnail_path,
                )
            except Exception as exc:
                prompt.thumbnail_path = None
                logger.warning(
                    "Thumbnail render failed | prompt_id=%s: %s",
                    prompt_id,
                    exc,
                )
            finally:
                cleanup_file(thumbnail_script_filename)

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
