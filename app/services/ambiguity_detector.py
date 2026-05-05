import os
from langchain_openai import ChatOpenAI
import config

class AmbiguityDetector:
    @staticmethod
    def analyze_prompt(text: str):
        # Simple length check (rule-based)
        if len(text.strip()) < 5:
            return False, "The request is too short. Please describe the object in more detail."

        # Verification via LLM (AI-based)
        api_key = getattr(config.Config, "LLM_API_KEY", os.getenv("LLM_API_KEY"))
        base_url = "https://api.groq.com/openai/v1"
        
        llm = ChatOpenAI(base_url=base_url, api_key=api_key, model="llama-3.3-70b-versatile")

        system_msg = (
            "You are a 3D modeling assistant. Your job is to decide if a user prompt is clear enough "
            "to create a 3D object in Blender. \n"
            "Rules for being 'CLEAR':\n"
            "- It names a specific object (e.g., 'table', 'sword', 'house').\n"
            "- It is not a random string of characters.\n"
            "- It is not contradictory (e.g., 'a square circle').\n\n"
            "If clear, respond with exactly 'CLEAR'.\n"
            "If not clear, respond with a short explanation in English why it's ambiguous."
        )

        try:
            response = llm.invoke([
                ("system", system_msg),
                ("human", text),
            ])
            decision = response.content.strip()

            if decision == "CLEAR":
                return True, None
            else:
                return False, decision
        except Exception as e:
            # If the AI fails, we pass the request as "clean" so as not to block the workflow
            return True, None