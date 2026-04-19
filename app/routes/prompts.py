from flask import Blueprint, request, jsonify, send_from_directory, current_app, session
from app.extensions import db
from app.models.prompt import PromptRequest, PromptStatus
from app.models.user import User
import os

prompts_bp = Blueprint("prompts", __name__)


@prompts_bp.route("", methods=["POST"])
def create_prompt():
    user_id = session.get("user_id")
    print("DEBUG session user_id:", user_id)

    if not user_id:
        return jsonify({
            "status": "error",
            "message": "Not authenticated"
        }), 401

    data = request.get_json()

    if not data or "prompt" not in data:
        return jsonify({
            "status": "error",
            "message": "Missing prompt"
        }), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found"
        }), 404

    prompt = PromptRequest(
        prompt_text=data["prompt"],
        status=PromptStatus.QUEUED,
        user_id=user.id
    )

    db.session.add(prompt)
    db.session.commit()

    # needs to stay here otherwise error
    from app.tasks.prompt_tasks import process_prompt_task
    process_prompt_task.delay(prompt.id)

    return jsonify({
        "id": prompt.id,
        "prompt": prompt.prompt_text,
        "status": prompt.status.value,
        "user_id": prompt.user_id
    }), 201


@prompts_bp.route("/<int:id>", methods=["GET"])
def get_prompt(id):
    prompt = PromptRequest.query.get(id)

    if not prompt:
        return jsonify({"error": "Prompt not found"}), 404

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    if prompt.user_id != user_id:
        return jsonify({"error": "Unauthorized access to this prompt"}), 403

    return jsonify({
        "id": prompt.id,
        "prompt": prompt.prompt_text,
        "status": prompt.status.value,
        "result_path": prompt.result_path,
        "error_message": prompt.error_message,
        "user_id": prompt.user_id,
        "username": prompt.user.username
    }), 200


@prompts_bp.route("/me", methods=["GET"])
def get_my_prompts():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    prompts = []
    for prompt in user.prompts:
        prompts.append({
            "id": prompt.id,
            "prompt": prompt.prompt_text,
            "status": prompt.status.value,
            "result_path": prompt.result_path,
            "error_message": prompt.error_message
        })

    return jsonify({
        "user_id": user.id,
        "username": user.username,
        "prompts": prompts
    }), 200


@prompts_bp.route("/<int:id>/download", methods=["GET"])
def download_prompt_file(id):
    prompt = PromptRequest.query.get(id)

    if not prompt:
        return jsonify({"error": "Prompt not found"}), 404

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    if prompt.user_id != user_id:
        return jsonify({"error": "Unauthorized access to this asset"}), 403

    if not prompt.result_path:
        return jsonify({"error": "No generated file for this prompt"}), 404

    filename = os.path.basename(prompt.result_path)
    models_dir = os.path.join(current_app.root_path, "..", "static", "models")
    models_dir = os.path.abspath(models_dir)
    file_path = os.path.join(models_dir, filename)

    if not os.path.exists(file_path):
        return jsonify({"error": f"File not found on server: {file_path}"}), 404

    return send_from_directory(models_dir, filename, as_attachment=True)


@prompts_bp.route("/<int:id>/file", methods=["GET"])
def get_prompt_file(id):
    prompt = PromptRequest.query.get(id)

    if not prompt:
        return jsonify({"error": "Prompt not found"}), 404

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    if prompt.user_id != user_id:
        return jsonify({"error": "Unauthorized access to this asset"}), 403

    if not prompt.result_path:
        return jsonify({"error": "No generated file for this prompt"}), 404

    filename = os.path.basename(prompt.result_path)
    models_dir = os.path.join(current_app.root_path, "..", "static", "models")
    models_dir = os.path.abspath(models_dir)
    file_path = os.path.join(models_dir, filename)

    if not os.path.exists(file_path):
        return jsonify({"error": f"File not found on server: {file_path}"}), 404

    return send_from_directory(models_dir, filename)