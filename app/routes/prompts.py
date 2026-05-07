from flask import Blueprint, request, jsonify, send_from_directory, current_app, session, Response
from app.extensions import db
from app.models.prompt import PromptRequest, PromptStatus
from app.models.user import User
from app.services.prompt_service import Parameters
from app.services.prompt_service import PromptService
from langchain_openai import ChatOpenAI
from app.models.feedback import GenerationFeedback, FeedbackRating
from sqlalchemy import func
import csv
import io
import os
import json
import config


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
    prompt_text = data.get("prompt")

    try:
        params_obj = Parameters(**data.get("parameters")) if "parameters" in data else None
        validated_params = params_obj.dict() if params_obj else None
    except Exception as e:
        return jsonify({"error": str(e)}), 400

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

    llm_for_classify = ChatOpenAI(
        base_url=current_app.config.get("LLM_BASE_URL", "https://api.groq.com/openai/v1"), 
        api_key=config.Config.LLM_API_KEY, 
        model=current_app.config.get("LLM_MODEL", "openai/gpt-oss-120b")
    )
    classification = PromptService.classify_intent(prompt_text, llm_for_classify)

    # BLOCK
    if classification["action"] == "block":
        return jsonify({"status": "error", "message": classification["reason"]}), 400

    # CLARIFY 
    if classification["action"] == "clarify":
        final_reason = classification.get("reason") or reason
        prompt = PromptRequest(
            parameters=validated_params,
            prompt_text=prompt_text,
            status=PromptStatus.AWAITING_CLARIFICATION, 
            error_message=final_reason,
            user_id=user.id
        )
        db.session.add(prompt)
        db.session.commit()

        return jsonify({
            "id": prompt.id,
            "status": "clarify",
            "message": final_reason
        }), 200 

    # PROCEED
    prompt = PromptRequest(
        prompt_text=prompt_text,
        parameters=validated_params,
        status=PromptStatus.QUEUED,
        user_id=user.id
    )

    db.session.add(prompt)
    db.session.commit()

    # needs to stay here otherwise error
    from app.tasks.prompt_tasks import process_prompt_task
    process_prompt_task.delay(prompt_id=prompt.id, parameters=data.get("parameters", {}))

    return jsonify({
        "id": prompt.id,
        "prompt": prompt.prompt_text,
        "status": prompt.status.value,
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


@prompts_bp.route("/<int:id>/feedback", methods=["POST"])
def create_feedback(id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    prompt = PromptRequest.query.get(id)
    if not prompt:
        return jsonify({"error": "Prompt not found"}), 404

    if prompt.user_id != user_id:
        return jsonify({"error": "Unauthorized access to this prompt"}), 403

    existing_feedback = GenerationFeedback.query.filter_by(
        prompt_id=prompt.id,
        user_id=user_id
    ).first()
    if existing_feedback:
        return jsonify({"error": "Feedback already submitted for this prompt"}), 409

    data = request.get_json() or {}

    rating = data.get("rating")
    if rating not in [r.value for r in FeedbackRating]:
        return jsonify({
            "error": "Invalid rating. Use positive, neutral or negative."
        }), 400

    accuracy_score = data.get("accuracy_score")
    quality_score = data.get("quality_score")

    for score_name, score_value in {
        "accuracy_score": accuracy_score,
        "quality_score": quality_score
    }.items():
        if score_value is not None and not (1 <= int(score_value) <= 5):
            return jsonify({
                "error": f"{score_name} must be between 1 and 5"
            }), 400

    feedback = GenerationFeedback(
        prompt_id=prompt.id,
        user_id=user_id,
        rating=FeedbackRating(rating),
        accuracy_score=accuracy_score,
        quality_score=quality_score,
        comment=data.get("comment"),
        llm_output=prompt.generated_code,
        parameters=prompt.parameters,
        result_path=prompt.result_path
    )

    db.session.add(feedback)
    db.session.commit()

    return jsonify({
        "id": feedback.id,
        "prompt_id": feedback.prompt_id,
        "user_id": feedback.user_id,
        "rating": feedback.rating.value,
        "accuracy_score": feedback.accuracy_score,
        "quality_score": feedback.quality_score,
        "comment": feedback.comment
    }), 201

@prompts_bp.route("/feedback/analytics", methods=["GET"])
def feedback_analytics():
  #  user_id = session.get("user_id")
  #  if not user_id:
   #     return jsonify({"error": "Not authenticated"}), 401

    feedbacks = GenerationFeedback.query.all()
    total_feedback = len(feedbacks)

    if total_feedback == 0:
        return jsonify({
            "total_feedback": 0,
            "success_rate": 0,
            "average_accuracy_score": None,
            "average_quality_score": None,
            "ratings": {},
            "comments": []
        }), 200

    ratings = {}
    success_count = 0
    accuracy_scores = []
    quality_scores = []
    comments = []

    for feedback in feedbacks:
        rating = feedback.rating.value
        ratings[rating] = ratings.get(rating, 0) + 1

        if feedback.accuracy_score is not None:
            accuracy_scores.append(feedback.accuracy_score)

        if feedback.quality_score is not None:
            quality_scores.append(feedback.quality_score)

        is_success = (
            feedback.rating.value == "positive"
            or (feedback.accuracy_score is not None and feedback.accuracy_score >= 4)
            or (feedback.quality_score is not None and feedback.quality_score >= 4)
        )

        if is_success:
            success_count += 1

        if feedback.comment and feedback.comment.strip():
            comments.append({
                "id": feedback.id,
                "prompt_id": feedback.prompt_id,
                "user_id": feedback.user_id,
                "rating": rating,
                "accuracy_score": feedback.accuracy_score,
                "quality_score": feedback.quality_score,
                "comment": feedback.comment,
                "prompt": feedback.prompt.prompt_text if feedback.prompt else None,
                "created_at": feedback.created_at.isoformat() if feedback.created_at else None
            })

    return jsonify({
        "total_feedback": total_feedback,
        "success_rate": round(success_count / total_feedback * 100, 2),
        "average_accuracy_score": round(sum(accuracy_scores) / len(accuracy_scores), 2) if accuracy_scores else None,
        "average_quality_score": round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else None,
        "ratings": ratings,
        "comments": comments
    }), 200

@prompts_bp.route("/feedback/export", methods=["GET"])
def export_feedback():
 #   user_id = session.get("user_id")
  #  if not user_id:
  #      return jsonify({"error": "Not authenticated"}), 401

    feedbacks = GenerationFeedback.query.all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "feedback_id",
        "prompt_id",
        "user_id",
        "rating",
        "accuracy_score",
        "quality_score",
        "success_label",
        "success_rate_value",
        "comment",
        "prompt_text",
        "parameters",
        "result_path",
        "is_modified_version",
        "parent_prompt_id",
        "created_at"
    ])

    for feedback in feedbacks:
        prompt = feedback.prompt

        # success_label = 1 means successful generation, 0 means not successful
        success_label = 1 if (
            feedback.rating.value == "positive"
            or (feedback.accuracy_score is not None and feedback.accuracy_score >= 4)
            or (feedback.quality_score is not None and feedback.quality_score >= 4)
        ) else 0

        is_modified_version = 1 if prompt.parent_prompt_id is not None else 0

        writer.writerow([
            feedback.id,
            feedback.prompt_id,
            feedback.user_id,
            feedback.rating.value,
            feedback.accuracy_score,
            feedback.quality_score,
            success_label,
            success_label,  # useful for Power BI average = success rate
            feedback.comment,
            prompt.prompt_text,
            json.dumps(feedback.parameters) if feedback.parameters else None,
            feedback.result_path,
            is_modified_version,
            prompt.parent_prompt_id,
            feedback.created_at.isoformat()
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=powerbi_generation_feedback.csv"
        }
    )
