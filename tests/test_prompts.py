import pytest
import sys
import os
from unittest.mock import MagicMock

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


def test_create_prompt_success(client, logged_in_user, mocker):
    mock_user = MagicMock()
    mock_user.id = 1

    mock_query = MagicMock()
    mock_query.get.return_value = mock_user

    mocker.patch("app.routes.prompts.User.query", mock_query)

    mocker.patch(
        "app.routes.prompts.PromptService.classify_intent",
        return_value={
            "action": "proceed",
            "family": "Simple Objects",
            "reason": None
        }
    )

    mocker.patch("app.tasks.prompt_tasks.process_prompt_task.delay")
    mocker.patch("app.db.session.add")
    mocker.patch("app.db.session.commit")

    response = client.post("/prompts", json={
        "prompt": "Draw a red cube",
        "category": "Simple Objects"
    })

    if response.status_code != 201:
        print("\nSTATUS:", response.status_code)
        print("DATA:", response.data.decode())

    assert response.status_code == 201
    assert response.get_json()["status"] == "queued"