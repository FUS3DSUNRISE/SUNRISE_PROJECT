from flask import Blueprint, request, jsonify

prompts_bp = Blueprint("prompts", __name__)

@prompts_bp.route("", methods=["POST"])
def create_prompt():
    data = request.get_json()

    if not data or "prompt" not in data:
        return jsonify({
            "status": "error",
            "message": "Missing prompt"
        }), 400 # bad request in http

    prompt_text = data["prompt"]

    return jsonify({
        "id": 1,
        "prompt": prompt_text,
        "status": "queued",
        "message": "Prompt stored successfully"
    }), 201 # created