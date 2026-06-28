import os
from uuid import uuid4
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.imported_asset import ImportedAsset
from app.services.asset_metadata_service import AssetMetadataService
from app.models.prompt import PromptRequest, PromptStatus
from app.services.prompt_service import Parameters


assets_bp = Blueprint("assets", __name__)

ALLOWED_EXTENSIONS = {"glb", "gltf", "obj"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@assets_bp.route("/import", methods=["POST"])
def import_asset():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "error": "Unsupported file format. Allowed formats: glb, gltf, obj"
        }), 400

    original_filename = secure_filename(file.filename)
    file_type = original_filename.rsplit(".", 1)[1].lower()
    unique_filename = f"{uuid4().hex}_{original_filename}"

    upload_dir = os.path.abspath(
        os.path.join(current_app.root_path, "..", "static", "models", "imported")
    )
    os.makedirs(upload_dir, exist_ok=True)

    absolute_file_path = os.path.join(upload_dir, unique_filename)
    file.save(absolute_file_path)

    metadata = AssetMetadataService.extract_metadata(
        absolute_file_path,
        original_filename=original_filename
    )

    relative_path = f"static/models/imported/{unique_filename}"

    imported_asset = ImportedAsset(
        filename=unique_filename,
        original_filename=original_filename,
        file_path=relative_path,
        file_type=file_type,
        user_id=user_id,
        metadata_json=metadata
    )

    db.session.add(imported_asset)
    db.session.commit()

    return jsonify({
        "id": imported_asset.id,
        "filename": imported_asset.filename,
        "original_filename": imported_asset.original_filename,
        "file_type": imported_asset.file_type,
        "file_path": imported_asset.file_path,
        "user_id": imported_asset.user_id,
        "message": "Asset imported successfully"
    }), 201


@assets_bp.route("/<int:id>", methods=["GET"])
def get_imported_asset(id):
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    asset = ImportedAsset.query.get(id)

    if not asset:
        return jsonify({"error": "Imported asset not found"}), 404

    if asset.user_id != user_id:
        return jsonify({"error": "Unauthorized access to this asset"}), 403

    return jsonify({
        "id": asset.id,
        "filename": asset.filename,
        "original_filename": asset.original_filename,
        "file_type": asset.file_type,
        "file_path": asset.file_path,
        "user_id": asset.user_id,
        "metadata": asset.metadata_json,
        "uploaded_at": asset.uploaded_at.isoformat() if asset.uploaded_at else None
    }), 200


@assets_bp.route("/me", methods=["GET"])
def get_my_imported_assets():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    assets = ImportedAsset.query.filter_by(user_id=user_id).order_by(
        ImportedAsset.uploaded_at.desc()
    ).all()

    return jsonify({
        "user_id": user_id,
        "assets": [
            {
                "id": asset.id,
                "filename": asset.filename,
                "original_filename": asset.original_filename,
                "file_type": asset.file_type,
                "file_path": asset.file_path,
                "metadata": asset.metadata_json,
                "uploaded_at": asset.uploaded_at.isoformat() if asset.uploaded_at else None
            }
            for asset in assets
        ]
    }), 200

@assets_bp.route("/<int:id>/metadata", methods=["GET"])
def get_asset_metadata(id):
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    asset = ImportedAsset.query.get(id)

    if not asset:
        return jsonify({"error": "Imported asset not found"}), 404

    if asset.user_id != user_id:
        return jsonify({"error": "Unauthorized access to this asset"}), 403

    return jsonify({
        "id": asset.id,
        "original_filename": asset.original_filename,
        "file_type": asset.file_type,
        "metadata": asset.metadata_json
    }), 200


@assets_bp.route("/<int:id>/modify", methods=["POST"])
def modify_imported_asset(id):
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401

    asset = ImportedAsset.query.get(id)

    if not asset:
        return jsonify({"error": "Imported asset not found"}), 404

    if asset.user_id != user_id:
        return jsonify({"error": "Unauthorized access to this asset"}), 403

    data = request.get_json() or {}
    command = data.get("command")
    incoming_parameters = data.get("parameters")

    if not command and not incoming_parameters:
        return jsonify({"error": "Missing modification command or parameters"}), 400

    validated_params = None
    if incoming_parameters:
        try:
            params_obj = Parameters(**incoming_parameters)
            validated_params = params_obj.dict()
        except Exception as exc:
            return jsonify({"error": str(exc)}), 400

    new_prompt = PromptRequest(
        prompt_text=f"Modify imported asset: {asset.original_filename}",
        modification_command=command,
        parameters=validated_params,
        status=PromptStatus.QUEUED,
        user_id=user_id,
        imported_asset_id=asset.id
    )

    db.session.add(new_prompt)
    db.session.commit()

    from app.tasks.prompt_tasks import process_prompt_task

    process_prompt_task.delay(
        prompt_id=new_prompt.id,
        parameters=validated_params or {},
        imported_asset_id=asset.id
    )

    return jsonify({
        "id": new_prompt.id,
        "status": new_prompt.status.value,
        "message": "Imported asset modification task started",
        "imported_asset_id": asset.id,
        "asset_path": asset.file_path,
        "metadata": asset.metadata_json,
        "command": command
    }), 201
