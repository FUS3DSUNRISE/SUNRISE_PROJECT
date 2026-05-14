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
        f"1. ANALYZE AND DECIDE: Look at the requested object: '{prompt_text}'.\n"
        f"Do NOT write python if/else statements. Evaluate the object yourself and output ONLY the corresponding commands:\n"
        f"- For a chair, output exactly: build_chair({s.width}, {s.depth}, {s.height})\n"
        f"- For a table or desk, output exactly: build_table({s.width}, {s.depth}, {s.height})\n"
        f"- For a tree or plant, output exactly: build_tree({s.width}, {s.depth}, {s.height})\n"
        f"- For ANYTHING ELSE: Build it yourself using Minecraft/Roblox logic! Break the object into primitive parts. Call `make_box`, `make_cylinder`, or `make_sphere` multiple times. Scale parts to fit roughly inside W:{s.width}m, H:{s.height}m, D:{s.depth}m. Connect them properly (Upper Z = Lower Z + Lower Height).\n\n"
        f"2. NO MODIFIERS: DO NOT use boolean modifiers or `apply_modifiers`. Use only the provided functions.\n\n"
        f"3. MATERIALS: Call `set_material('MatName', R, G, B, {m.roughness}, {m.metallic})` at the end. Invent logical RGB colors for the object.\n\n"
        f"4. CONCISENESS: Do NOT define `make_box`, `make_cylinder`, `make_sphere`, `set_material`, `build_chair`, or `build_table`. They are already defined for you. Just call them directly! Avoid comments and empty lines.\n\n"
        f"5. EXPORT: End the script exactly with:\n"
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