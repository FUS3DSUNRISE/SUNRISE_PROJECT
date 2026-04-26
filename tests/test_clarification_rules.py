import pytest

from app.services.clarification_rules import (
    ClarificationRules,
    build_fallback_followup_message,
)
from app.services.prompt_service import PromptService


def _case_names(ambiguity):
    return [case["name"] for case in ambiguity["cases"]]


@pytest.mark.parametrize(
    ("prompt_text", "is_clear", "detector_reason", "expected_primary_case"),
    [
        ("Generate something for my room", False, "object_unspecified", "object_unspecified"),
        ("a table", False, "object_subtype_ambiguous", "object_subtype_ambiguous"),
        ("a bookshelf", True, None, "dimensions_missing"),
        ("table and chairs", True, None, "item_count_ambiguous"),
        ("console", True, None, "multi_interpretation_term"),
    ],
)
def test_priority_ambiguity_cases_are_detected_with_questions_and_defaults(
    prompt_text,
    is_clear,
    detector_reason,
    expected_primary_case,
):
    ambiguity = ClarificationRules.analyze(
        prompt_text=prompt_text,
        selected_category="Simple Objects",
        classification={"action": "clarify", "family": "Furniture", "reason": expected_primary_case},
        is_clear=is_clear,
        detector_reason=detector_reason,
    )

    primary_case = ambiguity["cases"][0]

    assert ambiguity["detected"] is True
    assert ambiguity["handled_internally"] is True
    assert ambiguity["primary_case"] == expected_primary_case
    assert primary_case["name"] == expected_primary_case
    assert primary_case["clarification_question"]
    assert primary_case["default_resolution"]
    assert primary_case["recommended_action"] in {"ask_for_clarification", "proceed_with_defaults"}


def test_category_prompt_conflict_has_priority_over_secondary_missing_details():
    ambiguity = ClarificationRules.analyze(
        prompt_text="wooden chair",
        selected_category="Electronics",
        classification={"action": "clarify", "family": "Furniture", "reason": "category_prompt_conflict"},
        is_clear=True,
        detector_reason="category_prompt_conflict",
    )

    assert ambiguity["primary_case"] == "category_prompt_conflict"
    assert _case_names(ambiguity)[0] == "category_prompt_conflict"


def test_attribute_conflict_is_prioritized_before_subtype_or_style_details():
    ambiguity = ClarificationRules.analyze(
        prompt_text="minimalist ornate lamp",
        selected_category="Simple Objects",
        classification={"action": "clarify", "family": "Lighting", "reason": "attribute_conflict"},
        is_clear=True,
        detector_reason="attribute_conflict",
    )

    assert ambiguity["primary_case"] == "attribute_conflict"
    assert "object_subtype_ambiguous" in _case_names(ambiguity)


def test_clarified_prompt_removes_the_main_ambiguities():
    ambiguity = ClarificationRules.analyze(
        prompt_text="a modern wooden dining table for six people, 1.8 meters wide",
        selected_category="Simple Objects",
        classification={"action": "proceed", "family": "Furniture", "reason": None},
        is_clear=True,
        detector_reason=None,
    )

    assert ambiguity["detected"] is False
    assert ambiguity["primary_case"] is None
    assert ambiguity["cases"] == []


def test_fallback_followup_message_uses_object_from_prompt_before_category():
    ambiguity = ClarificationRules.analyze(
        prompt_text="a table",
        selected_category="Simple Objects",
        classification={"action": "clarify", "family": "Furniture", "reason": "object_subtype_ambiguous"},
        is_clear=False,
        detector_reason="object_subtype_ambiguous",
    )

    message = build_fallback_followup_message("a table", "Furniture", ambiguity)

    assert message.startswith("I generated a first version of the table")
    assert "What kind of table do you want?" in message


def test_generation_prompt_receives_ambiguity_defaults_in_priority_order():
    ambiguity = ClarificationRules.analyze(
        prompt_text="table and chairs",
        selected_category="Simple Objects",
        classification={"action": "clarify", "family": "Furniture", "reason": "item_count_ambiguous"},
        is_clear=True,
        detector_reason="item_count_ambiguous",
    )

    final_prompt = PromptService.create_final_prompt(
        user_query="table and chairs",
        category="Furniture",
        parameters={"_ambiguity": ambiguity},
    )

    item_count_position = final_prompt.index("item_count_ambiguous")
    subtype_position = final_prompt.index("object_subtype_ambiguous")

    assert "do not ask the user for clarification" in final_prompt
    assert "Use a standard composition" in final_prompt
    assert item_count_position < subtype_position
