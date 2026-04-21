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
        material_type = mat.get('type', 'plastic')
        roughness = mat.get('roughness', 0.5)
        final_prompt += f"Material: {material_type}, roughness: {roughness}. "
        
        final_prompt += "Professional studio lighting, 4k render, photorealistic, objective view."
        
        return final_prompt