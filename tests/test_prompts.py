import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

import pytest

import config
from app import create_app
from app.extensions import db
from app.models.prompt import PromptRequest, PromptStatus
from app.models.user import User
from app.services.clarification_rules import ClarificationRules
from app.services.prompt_service import PromptService


@pytest.fixture
def client():
    db_path = Path("tests") / f"test_prompts_{uuid.uuid4().hex}.db"
    config.Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path.resolve().as_posix()}"
    config.Config.LLM_API_KEY = "test-key"

    app = create_app()
    app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-key",
    })

    with app.app_context():
        db.drop_all()
        db.create_all()

        user = User(username="tester", email="tester@example.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()

        test_client = app.test_client()
        with test_client.session_transaction() as session:
            session["user_id"] = user.id

        yield test_client

        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        if db_path.exists():
            try:
                db_path.unlink()
            except PermissionError:
                pass


def test_create_prompt_success_queues_generation(client):
    with patch("app.routes.prompts.ChatOpenAI", return_value=object()), \
        patch("app.routes.prompts.AmbiguityDetector.analyze_prompt", return_value=(True, None)), \
        patch(
            "app.routes.prompts.PromptService.classify_intent",
            return_value={"action": "proceed", "family": "Simple Objects", "reason": None},
        ), \
        patch("app.tasks.prompt_tasks.process_prompt_task.delay") as delay:

        response = client.post("/prompts", json={
            "prompt": "Draw a red cube",
            "category": "Simple Objects",
        })

    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "queued"
    assert data["ambiguity"]["detected"] is False
    delay.assert_called_once()


def test_ambiguous_prompt_proceeds_with_internal_clarification_metadata(client):
    followup_message = (
        "I generated a standard table as a first version. "
        "To make it more accurate, do you want it to be a dining table?"
    )

    with patch("app.routes.prompts.ChatOpenAI", return_value=object()), \
        patch("app.routes.prompts.AmbiguityDetector.analyze_prompt", return_value=(False, "object_subtype_ambiguous")), \
        patch(
            "app.routes.prompts.PromptService.classify_intent",
            return_value={"action": "clarify", "family": "Furniture", "reason": "object_subtype_ambiguous"},
        ), \
        patch(
            "app.routes.prompts.PromptService.generate_followup_message",
            return_value=followup_message,
        ), \
        patch("app.tasks.prompt_tasks.process_prompt_task.delay") as delay:

        response = client.post("/prompts", json={
            "prompt": "a table",
            "category": "Simple Objects",
        })

    assert response.status_code == 201
    data = response.get_json()
    assert data["status"] == "queued"
    assert data["category"] == "Furniture"
    assert data["ambiguity"]["detected"] is True
    assert data["ambiguity"]["handled_internally"] is True
    assert data["ambiguity"]["primary_case"] == "object_subtype_ambiguous"
    assert data["ambiguity"]["user_followup_message"] == followup_message

    saved = PromptRequest.query.get(data["id"])
    assert saved.status == PromptStatus.QUEUED
    assert saved.category == "Furniture"
    assert saved.parameters["_ambiguity"]["primary_case"] == "object_subtype_ambiguous"
    assert saved.parameters["_ambiguity"]["user_followup_message"] == followup_message

    delay.assert_called_once()
    task_parameters = delay.call_args.kwargs["parameters"]
    assert task_parameters["_ambiguity"]["detected"] is True


def test_clarified_prompt_still_queues_generation_with_less_ambiguity(client):
    with patch("app.routes.prompts.ChatOpenAI", return_value=object()), \
        patch(
            "app.routes.prompts.PromptService.generate_followup_message",
            return_value="I generated a standard table as a first version. To make it more accurate, do you want it to be a dining table?",
        ), \
        patch("app.tasks.prompt_tasks.process_prompt_task.delay") as delay:

        with patch("app.routes.prompts.AmbiguityDetector.analyze_prompt", return_value=(False, "object_subtype_ambiguous")), \
            patch(
                "app.routes.prompts.PromptService.classify_intent",
                return_value={"action": "clarify", "family": "Furniture", "reason": "object_subtype_ambiguous"},
            ):
            ambiguous_response = client.post("/prompts", json={
                "prompt": "a table",
                "category": "Simple Objects",
            })

        with patch("app.routes.prompts.AmbiguityDetector.analyze_prompt", return_value=(True, None)), \
            patch(
                "app.routes.prompts.PromptService.classify_intent",
                return_value={"action": "proceed", "family": "Furniture", "reason": None},
            ):
            clarified_response = client.post("/prompts", json={
                "prompt": "a modern wooden dining table for six people, 1.8 meters wide",
                "category": "Simple Objects",
            })

    ambiguous_data = ambiguous_response.get_json()
    clarified_data = clarified_response.get_json()

    ambiguous_cases = {
        case["name"]
        for case in ambiguous_data["ambiguity"]["cases"]
    }
    clarified_cases = {
        case["name"]
        for case in clarified_data["ambiguity"]["cases"]
    }

    assert ambiguous_response.status_code == 201
    assert ambiguous_data["status"] == "queued"
    assert ambiguous_data["ambiguity"]["detected"] is True

    assert clarified_response.status_code == 201
    assert clarified_data["status"] == "queued"
    assert len(clarified_cases) < len(ambiguous_cases)
    assert "object_subtype_ambiguous" not in clarified_cases
    assert "style_missing" not in clarified_cases
    assert "material_missing" not in clarified_cases
    assert delay.call_count == 2


def test_blocked_prompt_returns_error_without_generation(client):
    with patch("app.routes.prompts.ChatOpenAI", return_value=object()), \
        patch("app.routes.prompts.AmbiguityDetector.analyze_prompt", return_value=(False, "Not a 3D object")), \
        patch(
            "app.routes.prompts.PromptService.classify_intent",
            return_value={"action": "block", "family": None, "reason": "Not a supported 3D object"},
        ), \
        patch("app.tasks.prompt_tasks.process_prompt_task.delay") as delay:

        response = client.post("/prompts", json={
            "prompt": "hello how are you",
            "category": "Simple Objects",
        })

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"
    assert PromptRequest.query.count() == 0
    delay.assert_not_called()


def test_prompt_service_uses_ambiguity_defaults_in_generation_prompt():
    ambiguity = ClarificationRules.analyze(
        prompt_text="a chair",
        selected_category="Simple Objects",
        classification={"action": "clarify", "family": "Furniture", "reason": "style_missing"},
        is_clear=True,
        detector_reason=None,
    )

    prompt = PromptService.create_final_prompt(
        user_query="a chair",
        category="Furniture",
        parameters={"_ambiguity": ambiguity},
    )

    assert "do not ask the user for clarification" in prompt
    assert "Use a modern, clean style by default" in prompt
    assert "Use medium, realistic real-world dimensions" in prompt


def test_followup_message_uses_llm_response_when_available():
    ambiguity = ClarificationRules.analyze(
        prompt_text="a table",
        selected_category="Simple Objects",
        classification={"action": "clarify", "family": "Furniture", "reason": "object_subtype_ambiguous"},
        is_clear=False,
        detector_reason="object_subtype_ambiguous",
    )
    llm_client = MagicMock()
    llm_client.invoke.return_value = SimpleNamespace(
        content="I generated a standard table as a first version. To make it more accurate, how would you like it to be?"
    )

    message = PromptService.generate_followup_message(
        prompt_text="a table",
        category="Furniture",
        ambiguity=ambiguity,
        llm_client=llm_client,
        fallback_message="fallback",
    )

    assert message.startswith("I generated a standard table")
    assert "how would you like it to be" in message
    llm_client.invoke.assert_called_once()


def test_followup_message_falls_back_to_mapping_when_llm_fails():
    ambiguity = ClarificationRules.analyze(
        prompt_text="a table",
        selected_category="Simple Objects",
        classification={"action": "clarify", "family": "Furniture", "reason": "object_subtype_ambiguous"},
        is_clear=False,
        detector_reason="object_subtype_ambiguous",
    )
    llm_client = MagicMock()
    llm_client.invoke.side_effect = RuntimeError("LLM unavailable")

    message = PromptService.generate_followup_message(
        prompt_text="a table",
        category="Furniture",
        ambiguity=ambiguity,
        llm_client=llm_client,
        fallback_message="I generated a first version of the furniture using sensible defaults. To make it more accurate, what kind of table do you want?",
    )

    assert message == "I generated a first version of the furniture using sensible defaults. To make it more accurate, what kind of table do you want?"


@pytest.mark.parametrize(
    ("prompt_text", "is_clear", "detector_reason", "expected_case"),
    [
        ("Generate something for my room", False, "object_unspecified", "object_unspecified"),
        ("a table", False, "object_subtype_ambiguous", "object_subtype_ambiguous"),
        ("a bookshelf", True, None, "dimensions_missing"),
        ("table and chairs", True, None, "item_count_ambiguous"),
        ("console", True, None, "multi_interpretation_term"),
    ],
)
def test_priority_ambiguity_cases_include_question_and_default_resolution(
    prompt_text,
    is_clear,
    detector_reason,
    expected_case,
):
    ambiguity = ClarificationRules.analyze(
        prompt_text=prompt_text,
        selected_category="Simple Objects",
        classification={"action": "clarify", "family": "Furniture", "reason": expected_case},
        is_clear=is_clear,
        detector_reason=detector_reason,
    )

    cases_by_name = {case["name"]: case for case in ambiguity["cases"]}

    assert ambiguity["detected"] is True
    assert expected_case in cases_by_name
    assert cases_by_name[expected_case]["clarification_question"]
    assert cases_by_name[expected_case]["default_resolution"]


def test_more_specific_prompt_reduces_ambiguity_cases():
    ambiguous = ClarificationRules.analyze(
        prompt_text="a table",
        selected_category="Simple Objects",
        classification={"action": "clarify", "family": "Furniture", "reason": "object_subtype_ambiguous"},
        is_clear=False,
        detector_reason="object_subtype_ambiguous",
    )
    clarified = ClarificationRules.analyze(
        prompt_text="a modern wooden dining table for six people, 1.8 meters wide",
        selected_category="Simple Objects",
        classification={"action": "proceed", "family": "Furniture", "reason": None},
        is_clear=True,
        detector_reason=None,
    )

    ambiguous_case_names = {case["name"] for case in ambiguous["cases"]}
    clarified_case_names = {case["name"] for case in clarified["cases"]}

    assert "object_subtype_ambiguous" in ambiguous_case_names
    assert "style_missing" in ambiguous_case_names
    assert "material_missing" in ambiguous_case_names
    assert len(clarified_case_names) < len(ambiguous_case_names)
    assert "object_subtype_ambiguous" not in clarified_case_names
    assert "style_missing" not in clarified_case_names
    assert "material_missing" not in clarified_case_names
