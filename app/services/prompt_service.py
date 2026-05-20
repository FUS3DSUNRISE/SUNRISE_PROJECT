import json
from pydantic import BaseModel, Field
from typing import Literal

class SizeParams(BaseModel):
    width: float = Field(..., ge=0.5, le=5)
    height: float = Field(..., ge=0.5, le=5)
    depth: float = Field(..., ge=0.5, le=5)

class GeometryParams(BaseModel):
    complexity: int = Field(..., ge=1, le=10)
    smoothness: int = Field(..., ge=1, le=100)

class MaterialParams(BaseModel):
    material_type: Literal["Plastic", "Metal", "Wood", "Glass"]
    roughness: float = Field(..., ge=0.0, le=1)
    metallic: float = Field(..., ge=0.0, le=1)

class Parameters(BaseModel):
    size: SizeParams
    geometry: GeometryParams
    material: MaterialParams

def build_llm_prompt(prompt_text: str, params: Parameters) -> str:
    s, g, m = params.size, params.geometry, params.material

    blender_rules = (
        f"1. PLAN FIRST (CHAIN OF THOUGHT): Before calling any functions, write a block of Python comments (starting with `#`) to act as your blueprint. Describe the ideal object in the requested style, break it down into primitive parts, and calculate their exact X, Y, Z coordinates and sizes to fit perfectly within W:{s.width}m, H:{s.height}m, D:{s.depth}m. Your subsequent code must strictly follow this plan.\n\n"
        f"2. ANALYZE AND DECIDE: Look at the requested object: '{prompt_text}'.\n"
        f"Do NOT write python if/else statements. Evaluate the object yourself and output ONLY the corresponding commands:\n"
        f"- For a chair, output exactly: build_chair({s.width}, {s.depth}, {s.height})\n"
        f"- For a table or desk, output exactly: build_table({s.width}, {s.depth}, {s.height})\n"
        f"- For a tree or plant, output exactly: build_tree({s.width}, {s.depth}, {s.height})\n"
        f"- For a sofa or couch, output exactly: build_sofa({s.width}, {s.depth}, {s.height})\n"
        f"- For a bed, output exactly: build_bed({s.width}, {s.depth}, {s.height})\n"
        f"- For a lamp, output exactly: build_lamp({s.width}, {s.depth}, {s.height})\n"
        f"- For a car, output exactly: build_car({s.width}, {s.depth}, {s.height})\n"
        f"- For a laptop or computer, output exactly: build_laptop({s.width}, {s.depth}, {s.height})\n"
        f"- For a wardrobe or closet, output exactly: build_wardrobe({s.width}, {s.depth}, {s.height})\n"
        f"- For a cat, output exactly: build_cat({s.width}, {s.depth}, {s.height})\n"
        f"- For a pallet, output exactly: build_pallet({s.width}, {s.depth}, {s.height})\n"
        f"- For a screw or nail, output exactly: build_screw({s.width}, {s.depth}, {s.height})\n"
        f"- For ANYTHING ELSE: Build it yourself using Minecraft/Roblox logic! Break the object into primitive parts. Call `make_box(name, w, d, h, x, y, z)`, `make_cylinder(name, r, h, x, y, z)`, `make_sphere(name, r, x, y, z)`, `make_cone(name, r, h, x, y, z)`, or `make_torus(name, r_major, r_minor, x, y, z)` multiple times. Scale parts to fit roughly inside W:{s.width}m, H:{s.height}m, D:{s.depth}m. HORIZONTAL THINKING: Use the X and Y axes to distribute parts left/right and front/back! Do NOT just stack everything vertically. For example, place wheels on the sides using X/Y offsets, not stacked underneath. Only use vertical stacking (Upper Z = Lower Z + Lower Height) for parts that actually sit on top of each other.\n\n"
        f"3. NO MODIFIERS: DO NOT use boolean modifiers or `apply_modifiers`. Use only the provided functions.\n\n"
        f"4. MATERIALS: Call `set_material('MatName', R, G, B, {m.roughness}, {m.metallic}, 'ObjectName')` to color specific parts (e.g. 'Foliage', 'Trunk'). If 'ObjectName' is omitted, it colors all uncolored parts.\n\n"
        f"5. CONCISENESS: Do NOT define `make_box`, `make_cylinder`, `make_sphere`, `make_cone`, `make_torus`, `set_material`, `build_chair`, `build_table`, `build_tree`, `build_sofa`, `build_bed`, `build_lamp`, `build_car`, `build_laptop`, `build_wardrobe`, `build_cat`, `build_pallet`, or `build_screw`. They are already defined for you. Just call them directly! Keep the active code concise and avoid unnecessary empty lines.\n\n"
        f"6. EXPORT: End the script exactly with:\n"
        "bpy.ops.object.select_all(action='DESELECT')\n"
        "mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']\n"
        "for obj in mesh_objects: obj.select_set(True)\n"
        "if mesh_objects: bpy.context.view_layer.objects.active = mesh_objects[0]\n"
        "bpy.ops.export_scene.gltf(filepath='static/models/result.glb', export_format='GLB')\n"
    )

    return f"Write a Blender Python script for: {prompt_text}\n\nRULES:\n{blender_rules}\n\nSTART YOUR RESPONSE DIRECTLY WITH YOUR SCRIPT. DO NOT IMPORT BPY OR WRITE HELPER FUNCTIONS."

class PromptService:
    @staticmethod
    def classify_intent(prompt_text, llm_client):
        system_prompt = (
            "You are a 3D object classifier. Analyze the user prompt.\n\n"
            "Return JSON only:\n"
            "{\n"
            "  'action': 'proceed' | 'clarify' | 'block',\n"
            "  'reason': 'Explanation'\n"
            "}\n"
            "Rules:\n"
            "- Known object: proceed.\n"
            "- Ambiguous/Unknown: clarify.\n"
            "- Not an object/Nonsense: block."
        )

        try:
            response = llm_client.invoke([
                ("system", system_prompt),
                ("human", prompt_text),
            ])
            clean_content = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_content)
        except Exception:
            return {"action": "proceed", "reason": None}

    @staticmethod
    def generate_final_prompt(user_prompt, parameters):
        return user_prompt

    @staticmethod
    def create_final_prompt(user_query, parameters=None):
        return PromptService.generate_final_prompt(
            user_prompt=user_query,
            parameters=parameters or {},
        )