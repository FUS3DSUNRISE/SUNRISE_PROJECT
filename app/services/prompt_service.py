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
