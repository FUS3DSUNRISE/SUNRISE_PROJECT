import threading
import time
from flask import current_app
from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.prompt import PromptRequest, PromptStatus



prompts_bp = Blueprint("prompts", __name__)

def mock_process_prompt(app, prompt_id):
    with app.app_context():
        prompt = PromptRequest.query.get(prompt_id)

        if not prompt:
            return

        prompt.status = PromptStatus.PROCESSING
        db.session.commit()

        time.sleep(2)

        prompt.status = PromptStatus.COMPLETED
        prompt.result_path = "files/result.glb"
        db.session.commit()


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

    thread = threading.Thread(
    target=mock_process_prompt,
    args=(current_app._get_current_object(), prompt.id)
)
    thread.start()

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




