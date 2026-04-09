from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.prompt import PromptRequest, PromptStatus



prompts_bp = Blueprint("prompts", __name__)



@prompts_bp.route("", methods=["POST"])
def create_prompt():
    data = request.get_json()

    if not data or "prompt" not in data:
        return jsonify({
            "status": "error",
            "message": "Missing prompt"
        }), 400 # bad request in http

    prompt = PromptRequest(
        prompt_text=data["prompt"],
        status=PromptStatus.QUEUED
    )

    db.session.add(prompt)
    db.session.commit()

    from app.tasks.prompt_tasks import process_prompt_task
    process_prompt_task.delay(prompt.id)

    return jsonify({
        "id": prompt.id,
        "prompt": prompt.prompt_text,
        "status": prompt.status.value
    }), 201 # created


@prompts_bp.route("/<int:id>", methods=["GET"])
def get_prompt(id):
    prompt = PromptRequest.query.get(id)

    if not prompt:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "id": prompt.id,
        "prompt": prompt.prompt_text,
        "status": prompt.status.value,
        "result_path": prompt.result_path,
        "error_message": prompt.error_message
    })




