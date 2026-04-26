from flask import Blueprint, request, jsonify, send_from_directory, current_app, session
from app.extensions import db
from app.models.prompt import PromptRequest, PromptStatus
from app.models.user import User
from app.services.prompt_service import Parameters
from app.services.ambiguity_detector import AmbiguityDetector
from app.services.clarification_rules import ClarificationRules, build_fallback_followup_message
from app.services.prompt_service import PromptService
from langchain_openai import ChatOpenAI
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


    data = request.get_json(silent=True)
    if not data or "prompt" not in data:
        return jsonify({
            "status": "error",
            "message": "Missing prompt"
        }), 400

    category = data.get("category", "Simple Objects")
    prompt_text = data.get("prompt", "").strip()
    print(f"DEBUG: Data received from frontend: {data}")
    print(f"DEBUG: Category extracted: {category}")

    try:
        raw_parameters = data.get("parameters") or {}
        params_obj = Parameters(**raw_parameters) if raw_parameters else None
        validated_params = params_obj.dict() if params_obj else None
    except Exception as e:
        return jsonify({"error": str(e)}), 400


    user = User.query.get(user_id)
    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found"
        }), 404


    is_clear, reason = AmbiguityDetector.analyze_prompt(prompt_text)
    llm_for_classify = ChatOpenAI(
        base_url=current_app.config.get("LLM_BASE_URL", "https://api.groq.com/openai/v1"), 
        api_key=current_app.config.get("LLM_API_KEY", ""), 
        model=current_app.config.get("LLM_MODEL", "llama-3.3-70b-versatile")
    )
    classification = PromptService.classify_intent(prompt_text, llm_for_classify)

    if classification.get("action") == "block":
        return jsonify({"status": "error", "message": classification.get("reason")}), 400

    # PROCEED
    detected_category = classification.get("family") or category
    ambiguity = ClarificationRules.analyze(
        prompt_text=prompt_text,
        selected_category=category,
        classification=classification,
        is_clear=is_clear,
        detector_reason=reason,
    )
    fallback_followup_message = build_fallback_followup_message(
        prompt_text=prompt_text,
        category=detected_category,
        ambiguity=ambiguity,
    )
    followup_message = PromptService.generate_followup_message(
        prompt_text=prompt_text,
        category=detected_category,
        ambiguity=ambiguity,
        llm_client=llm_for_classify,
        fallback_message=fallback_followup_message,
    )
    if followup_message:
        ambiguity["user_followup_message"] = followup_message

    generation_parameters = dict(validated_params or {})
    generation_parameters["category"] = detected_category
    if ambiguity["detected"]:
        generation_parameters["_ambiguity"] = ambiguity


    prompt = PromptRequest(
        parameters=generation_parameters,
        prompt_text=prompt_text,
        category=detected_category,
        status=PromptStatus.QUEUED,
        user_id=user.id
    )


    db.session.add(prompt)
    db.session.commit()


    # needs to stay here otherwise error
    from app.tasks.prompt_tasks import process_prompt_task
    process_prompt_task.delay(prompt_id=prompt.id, parameters=generation_parameters)

    return jsonify({
        "id": prompt.id,
        "prompt": prompt.prompt_text,
        "category": prompt.category,
        "status": prompt.status.value,
        "ambiguity": ambiguity,
        "user_id": prompt.user_id
    }), 201

def get_root_prompt(prompt):
    current = prompt
    while current.parent_prompt is not None:
        current = current.parent_prompt
    return current


def collect_version_history(prompt):
    versions = []

    def dfs(node):
        versions.append({
            "id": node.id,
            "parent_prompt_id": node.parent_prompt_id,
            "status": node.status.value,
            "result_path": node.result_path,
            "created_at": node.created_at.isoformat() if node.created_at else None
        })

        children = sorted(node.refined_versions, key=lambda p: p.created_at or 0)
        for child in children:
            dfs(child)

    root = get_root_prompt(prompt)
    dfs(root)

    return versions, root

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

    version_history, root_prompt = collect_version_history(prompt)

    return jsonify({
        "id": prompt.id,
        "prompt": prompt.prompt_text,
        "category": prompt.category,
        "status": prompt.status.value,
        "result_path": prompt.result_path,
        "error_message": prompt.error_message,
        "user_id": prompt.user_id,
        "username": prompt.user.username,
        "parent_prompt_id": prompt.parent_prompt_id,
        "root_prompt_id": root_prompt.id,
        "version_history": version_history
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
            "category": prompt.category,
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

@prompts_bp.route("/<int:id>/modify", methods=["POST"])
def modify_prompt(id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    original_prompt = PromptRequest.query.get_or_404(id)

    if original_prompt.user_id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json() or {}
    command = data.get("command")
    incoming_parameters = data.get("parameters")

    if not command and not incoming_parameters:
        return jsonify({"error": "Missing command or parameters"}), 400

    validated_params = original_prompt.parameters

    if incoming_parameters:
        try:
            params_obj = Parameters(**incoming_parameters)
            validated_params = params_obj.dict()
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    new_prompt = PromptRequest(
        prompt_text=original_prompt.prompt_text,
        parameters=validated_params,
        category=original_prompt.category,
        status=PromptStatus.QUEUED,
        user_id=user_id,
        parent_prompt_id=original_prompt.id,
        modification_command=command
    )

    db.session.add(new_prompt)
    db.session.commit()

    from app.tasks.prompt_tasks import process_prompt_task
    process_prompt_task.delay(
        prompt_id=new_prompt.id,
        parameters=new_prompt.parameters,
        fast_track_id=original_prompt.id
    )

    return jsonify({
        "id": new_prompt.id,
        "status": new_prompt.status.value,
        "message": "Modification started",
        "parent_id": original_prompt.id
    }), 201
