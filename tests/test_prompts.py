import pytest
import sys
import os
from unittest.mock import MagicMock, patch

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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
        result_path="/static/models/prompt_root.glb"
    )
    db.session.add(root)
    db.session.flush()

    middle = PromptRequest(
        prompt_text="base chair",
        status=PromptStatus.COMPLETED,
        user_id=user.id,
        parent_prompt_id=root.id,
        modification_command="make it taller",
        result_path="/static/models/prompt_middle.glb"
    )
    sibling = PromptRequest(
        prompt_text="base chair",
        status=PromptStatus.COMPLETED,
        user_id=user.id,
        parent_prompt_id=root.id,
        modification_command="make it wider",
        result_path="/static/models/prompt_sibling.glb"
    )
    db.session.add_all([middle, sibling])
    db.session.flush()

    leaf = PromptRequest(
        prompt_text="base chair",
        status=PromptStatus.COMPLETED,
        user_id=user.id,
        parent_prompt_id=middle.id,
        modification_command="make it metallic",
        result_path="/static/models/prompt_leaf.glb"
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
