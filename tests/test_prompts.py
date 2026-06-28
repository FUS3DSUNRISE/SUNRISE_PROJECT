import pytest
import sys
import os
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = Path(os.path.abspath(os.path.join(CURRENT_DIR, "..")))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

mock_service = MagicMock()
mock_service.classify_intent.return_value = {
    "action": "proceed",
    "family": "Simple Objects",
    "reason": None
}

sys.modules['app.services.prompt_service'] = MagicMock(
    PromptService=MagicMock(return_value=mock_service)
)
sys.modules['app.tasks.prompt_tasks'] = MagicMock()

from app import create_app, db
from app.models.feedback import FeedbackRating, GenerationFeedback
from app.models.imported_asset import ImportedAsset
from app.models.prompt import PromptRequest, PromptStatus
from app.models.user import User


@pytest.fixture
def client():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-key"
    })

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def logged_in_user(client):
    with client.session_transaction() as sess:
        sess['user_id'] = 1
    return 1


def test_create_prompt_success(client, logged_in_user):
    mock_user = MagicMock()
    mock_user.id = 1

    mock_query = MagicMock()
    mock_query.get.return_value = mock_user

    with (
        patch("app.routes.prompts.User.query", mock_query),
        patch(
            "app.routes.prompts.PromptService.classify_intent",
            return_value={
                "action": "proceed",
                "family": "Simple Objects",
                "reason": None
            }
        ),
        patch("app.tasks.prompt_tasks.process_prompt_task.delay"),
        patch("app.db.session.add"),
        patch("app.db.session.commit")
    ):
        response = client.post("/prompts", json={
            "prompt": "Draw a red cube",
            "category": "Simple Objects"
        })

    if response.status_code != 201:
        print("\nSTATUS:", response.status_code)
        print("DATA:", response.data.decode())

    assert response.status_code == 201
    assert response.get_json()["status"] == "queued"


def create_user_with_prompt_tree():
    suffix = uuid.uuid4().hex

    user = User(
        username="history-user",
        email="history@example.com",
        password_hash="hash"
    )
    db.session.add(user)
    db.session.flush()

    root = PromptRequest(
        prompt_text="base chair",
        status=PromptStatus.COMPLETED,
        user_id=user.id,
        result_path=f"/static/models/prompt_root_{suffix}.glb",
        thumbnail_path=f"/static/models/thumbnails/prompt_root_{suffix}.png"
    )
    db.session.add(root)
    db.session.flush()

    middle = PromptRequest(
        prompt_text="base chair",
        status=PromptStatus.COMPLETED,
        user_id=user.id,
        parent_prompt_id=root.id,
        modification_command="make it taller",
        result_path=f"/static/models/prompt_middle_{suffix}.glb",
        thumbnail_path=f"/static/models/thumbnails/prompt_middle_{suffix}.png"
    )
    sibling = PromptRequest(
        prompt_text="base chair",
        status=PromptStatus.COMPLETED,
        user_id=user.id,
        parent_prompt_id=root.id,
        modification_command="make it wider",
        result_path=f"/static/models/prompt_sibling_{suffix}.glb",
        thumbnail_path=f"/static/models/thumbnails/prompt_sibling_{suffix}.png"
    )
    db.session.add_all([middle, sibling])
    db.session.flush()

    leaf = PromptRequest(
        prompt_text="base chair",
        status=PromptStatus.COMPLETED,
        user_id=user.id,
        parent_prompt_id=middle.id,
        modification_command="make it metallic",
        result_path=f"/static/models/prompt_leaf_{suffix}.glb",
        thumbnail_path=f"/static/models/thumbnails/prompt_leaf_{suffix}.png"
    )
    db.session.add(leaf)
    db.session.flush()

    feedback = GenerationFeedback(
        prompt_id=middle.id,
        user_id=user.id,
        rating=FeedbackRating.POSITIVE
    )
    db.session.add(feedback)
    db.session.commit()

    return user, root, middle, sibling, leaf


def _write_media_file(relative_path: str) -> Path:
    file_path = PROJECT_ROOT / Path(relative_path.lstrip("/\\"))
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(b"test-file")
    return file_path


def test_delete_prompt_version_removes_one_version_and_promotes_children(client):
    with client.application.app_context():
        user, root, middle, sibling, leaf = create_user_with_prompt_tree()
        user_id = user.id
        root_id = root.id
        middle_id = middle.id
        sibling_id = sibling.id
        leaf_id = leaf.id

    with client.session_transaction() as sess:
        sess["user_id"] = user_id

    response = client.delete(f"/prompts/{middle_id}")

    assert response.status_code == 200

    with client.application.app_context():
        assert db.session.get(PromptRequest, middle_id) is None
        assert db.session.get(GenerationFeedback, 1) is None

        promoted_leaf = db.session.get(PromptRequest, leaf_id)
        sibling_prompt = db.session.get(PromptRequest, sibling_id)

        assert promoted_leaf.parent_prompt_id == root_id
        assert sibling_prompt.parent_prompt_id == root_id

    history_response = client.get(f"/prompts/{root_id}")
    history_ids = [item["id"] for item in history_response.get_json()["version_history"]]

    assert history_response.status_code == 200
    assert history_ids == [root_id, sibling_id, leaf_id]


def test_get_prompt_thumbnail_returns_static_image_file(client):
    thumbnail_path = None
    response = None
    with client.application.app_context():
        user, root, *_ = create_user_with_prompt_tree()
        user_id = user.id
        root_id = root.id
        thumbnail_path = _write_media_file(root.thumbnail_path)
        expected_bytes = b"thumbnail-bytes"
        thumbnail_path.write_bytes(expected_bytes)

    try:
        with client.session_transaction() as sess:
            sess["user_id"] = user_id

        response = client.get(f"/prompts/{root_id}/thumbnail")

        assert response.status_code == 200
        assert response.data == expected_bytes
        assert response.mimetype == "image/png"
    finally:
        if thumbnail_path is not None:
            if response is not None:
                response.close()
            thumbnail_path.unlink(missing_ok=True)


def test_get_prompt_history_includes_static_thumbnail_paths(client):
    with client.application.app_context():
        user, root, middle, sibling, leaf = create_user_with_prompt_tree()
        user_id = user.id
        root_id = root.id
        root_thumbnail_path = root.thumbnail_path
        middle_thumbnail_path = middle.thumbnail_path
        sibling_thumbnail_path = sibling.thumbnail_path
        leaf_thumbnail_path = leaf.thumbnail_path

    with client.session_transaction() as sess:
        sess["user_id"] = user_id

    response = client.get(f"/prompts/{root_id}")

    assert response.status_code == 200
    version_history = response.get_json()["version_history"]
    assert version_history[0]["thumbnail_path"] == root_thumbnail_path
    assert {
        item["thumbnail_path"] for item in version_history[1:]
    } == {middle_thumbnail_path, sibling_thumbnail_path, leaf_thumbnail_path}


def test_delete_prompt_version_removes_only_deleted_version_files(client):
    with client.application.app_context():
        user, root, middle, sibling, leaf = create_user_with_prompt_tree()
        user_id = user.id
        middle_id = middle.id

        root_result = _write_media_file(root.result_path)
        root_thumbnail = _write_media_file(root.thumbnail_path)
        middle_result = _write_media_file(middle.result_path)
        middle_thumbnail = _write_media_file(middle.thumbnail_path)
        sibling_result = _write_media_file(sibling.result_path)
        sibling_thumbnail = _write_media_file(sibling.thumbnail_path)
        leaf_result = _write_media_file(leaf.result_path)
        leaf_thumbnail = _write_media_file(leaf.thumbnail_path)

    with client.session_transaction() as sess:
        sess["user_id"] = user_id

    response = client.delete(f"/prompts/{middle_id}")

    assert response.status_code == 200
    assert not middle_result.exists()
    assert not middle_thumbnail.exists()
    assert root_result.exists()
    assert root_thumbnail.exists()
    assert sibling_result.exists()
    assert sibling_thumbnail.exists()
    assert leaf_result.exists()
    assert leaf_thumbnail.exists()

    for file_path in [
        root_result,
        root_thumbnail,
        sibling_result,
        sibling_thumbnail,
        leaf_result,
        leaf_thumbnail,
    ]:
        file_path.unlink(missing_ok=True)


def test_delete_prompt_history_removes_all_media_files(client):
    with client.application.app_context():
        user, root, middle, sibling, leaf = create_user_with_prompt_tree()
        user_id = user.id
        root_id = root.id
        middle_id = middle.id
        sibling_id = sibling.id
        leaf_id = leaf.id

        media_files = [
            _write_media_file(root.result_path),
            _write_media_file(root.thumbnail_path),
            _write_media_file(middle.result_path),
            _write_media_file(middle.thumbnail_path),
            _write_media_file(sibling.result_path),
            _write_media_file(sibling.thumbnail_path),
            _write_media_file(leaf.result_path),
            _write_media_file(leaf.thumbnail_path),
        ]

    with client.session_transaction() as sess:
        sess["user_id"] = user_id

    response = client.delete(f"/prompts/{root_id}/history")

    assert response.status_code == 200
    assert set(response.get_json()["deleted_ids"]) == {root_id, middle_id, sibling_id, leaf_id}
    assert all(not file_path.exists() for file_path in media_files)


def test_history_restore_handler_updates_prompt_and_parameters_in_ui_logic():
    page_source = (PROJECT_ROOT / "frontend" / "app" / "page.tsx").read_text(encoding="utf-8")

    assert "setPrompt(historyPrompt.prompt ?? \"\")" in page_source
    assert "setModifyCommand(historyPrompt.modification_command ?? \"\")" in page_source
    assert "setErrorMessage(historyPrompt.error_message)" in page_source
    assert "setFeedbackSubmittedPromptId(null)" in page_source
    assert "setParameters(toModelParameters(historyPrompt.parameters))" in page_source
    assert "setResult({" in page_source
    assert "setStatus(getGenerationStatus(historyPrompt.status))" in page_source
    assert "setIsHistoryOpen(false)" in page_source


def test_modify_imported_asset_persists_parameters_and_passes_them_to_task(client):
    class _FakeParameters:
        def __init__(self, **kwargs):
            self._data = kwargs

        def dict(self):
            return self._data

    with client.application.app_context():
        user = User(username="import-user", email="import@example.com", password_hash="hash")
        db.session.add(user)
        db.session.flush()

        imported_asset = ImportedAsset(
            filename="asset.glb",
            original_filename="asset.glb",
            file_path="static/models/imported/asset.glb",
            file_type="glb",
            user_id=user.id,
            metadata_json={},
        )
        db.session.add(imported_asset)
        db.session.commit()
        asset_id = imported_asset.id
        user_id = user.id

    with client.session_transaction() as sess:
        sess["user_id"] = user_id

    parameters = {
        "size": {"width": 2.0, "height": 1.5, "depth": 1.2},
        "geometry": {"complexity": 6, "smoothness": 28},
        "material": {"material_type": "Wood", "roughness": 0.35, "metallic": 0.1},
    }

    with (
        patch("app.routes.assets.Parameters", _FakeParameters),
        patch("app.tasks.prompt_tasks.process_prompt_task.delay") as delay_mock,
    ):
        response = client.post(
            f"/assets/{asset_id}/modify",
            json={
                "command": "Make it wider and taller",
                "parameters": parameters,
            },
        )

    assert response.status_code == 201

    with client.application.app_context():
        prompt = db.session.get(PromptRequest, response.get_json()["id"])
        assert prompt is not None
        assert prompt.parameters == parameters
        assert prompt.imported_asset_id == asset_id

    delay_mock.assert_called_once()
    called_kwargs = delay_mock.call_args.kwargs
    assert called_kwargs["imported_asset_id"] == asset_id
    assert called_kwargs["parameters"] == parameters


def test_delete_prompt_history_removes_complete_card(client):
    with client.application.app_context():
        user, root, middle, sibling, leaf = create_user_with_prompt_tree()
        user_id = user.id
        root_id = root.id
        ids = {root.id, middle.id, sibling.id, leaf.id}

    with client.session_transaction() as sess:
        sess["user_id"] = user_id

    response = client.delete(f"/prompts/{root_id}/history")

    assert response.status_code == 200
    assert set(response.get_json()["deleted_ids"]) == ids

    with client.application.app_context():
        assert PromptRequest.query.count() == 0
        assert GenerationFeedback.query.count() == 0

    history_response = client.get("/prompts/me")

    assert history_response.status_code == 200
    assert history_response.get_json()["prompts"] == []
