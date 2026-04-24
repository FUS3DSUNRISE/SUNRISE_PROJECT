import json
from pydantic import BaseModel, Field
from typing import Literal


CATEGORY_HINTS = {
    "Simple Objects": (
        "Focus on a single clear object with stable proportions, clean geometry, "
        "and no unnecessary extra parts."
    ),
    "Furniture": (
        "Prioritize practical proportions, sturdy support elements, and dimensions "
        "consistent with real household furniture."
    ),
    "Architecture": (
        "Use architectural scale, structural thickness, and clean orthogonal forms "
        "unless the prompt explicitly asks for something organic."
    ),
    "Decorative Objects": (
        "Prioritize silhouette, ornamental detail, and presentation-ready proportions "
        "while keeping the mesh clean and stable."
    ),
    "Electronics": (
        "Use compact manufactured proportions, precise edges, and recognizable product-like forms."
    ),
    "Kitchenware": (
        "Assume household scale and functional everyday proportions for mugs, plates, bowls, "
        "bottles, utensils, and small appliances."
    ),
    "Lighting": (
        "Preserve a stable base or support, coherent lamp proportions, and functional object structure."
    ),
    "Vehicles": (
        "Use recognizable vehicle proportions, grounded wheel placement when relevant, and a stable body structure."
    ),
    "Characters / Creatures": (
        "Keep anatomy or body-part hierarchy readable with a balanced silhouette and stable pose."
    ),
    "Plants": (
        "Use organic proportions, natural variation, and a stable trunk, stem, or pot structure when relevant."
    ),
    "Clothing / Accessories": (
        "Model the item as a standalone wearable object with clear form, practical proportions, and recognizable use."
    ),
    "Tools / Equipment": (
        "Favor durable manufactured shapes, functional proportions, and clear separation of handle, body, and support parts."
    ),
    "Toys / Game Props": (
        "Use stylized but readable proportions, simplified forms, and game-ready silhouette clarity."
    ),
    "Office Items": (
        "Use desk-scale dimensions and practical everyday forms for stationery, desk accessories, and office hardware."
    ),
    "Bathroom Items": (
        "Use domestic bathroom scale, functional geometry, and clean practical proportions."
    ),
}

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


    return (
        f"Generate a Blender Python script for: {prompt_text}\n\n"
        f"STRICT PARAMETERS:\n"
        f"Size:     width={s.width}m, height={s.height}m, depth={s.depth}m\n"
        f"Geometry: complexity={g.complexity}/10, smoothness={g.smoothness}/100\n"
        f"Material: type={m.material_type}, roughness={m.roughness}, metallic={m.metallic}"
    )

class PromptService:
    @staticmethod
    def classify_intent(prompt_text, llm_client):
        families_list = list(CATEGORY_HINTS.keys())

        system_prompt = (
            "You are a 3D object classifier. Analyze the user prompt.\n"
            f"Available Families: {', '.join(families_list)}\n\n"
            "Return JSON only:\n"
            "{\n"
            "  'action': 'proceed' | 'clarify' | 'block',\n"
            "  'family': 'Family Name' | null,\n"
            "  'reason': 'Explanation why you need clarification or why it is blocked'\n"
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
            return {"action": "proceed", "family": "Simple Objects", "reason": None}

    @staticmethod
    def generate_final_prompt(user_prompt, category, parameters):

        final_prompt = f"High-quality 3D model of a {category}: {user_prompt}. "

        category_hint = CATEGORY_HINTS.get(category)
        if category_hint:
            final_prompt += f"Category guidance: {category_hint} "
        
        # geometry details
        geom = parameters.get('geometry', {})
        complexity = geom.get('complexity', 5)
        if complexity > 7:
            final_prompt += "Intricate details, high poly count, complex structure. "
        
        # add material details
        mat = parameters.get('material', {})
        material_type = mat.get('material_type', mat.get('type', 'plastic'))
        roughness = mat.get('roughness', 0.5)
        final_prompt += f"Material: {material_type}, roughness: {roughness}. "
        
        final_prompt += "Professional studio lighting, 4k render, photorealistic, objective view."
        
        return final_prompt

    @staticmethod
    def create_final_prompt(user_query, category, parameters=None):
        return PromptService.generate_final_prompt(
            user_prompt=user_query,
            category=category,
            parameters=parameters or {},
        )
