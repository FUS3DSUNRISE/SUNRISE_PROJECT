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


    return (
        f"Generate a Blender Python script for: {prompt_text}\n\n"
        f"STRICT PARAMETERS:\n"
        f"Size:     width={s.width}m, height={s.height}m, depth={s.depth}m\n"
        f"Geometry: complexity={g.complexity}/10, smoothness={g.smoothness}/100\n"
        f"Material: type={m.material_type}, roughness={m.roughness}, metallic={m.metallic}"
    )

class PromptService:
    @staticmethod
    def generate_final_prompt(user_prompt, category, parameters):

        final_prompt = f"High-quality 3D model of a {category}: {user_prompt}. "
        
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

