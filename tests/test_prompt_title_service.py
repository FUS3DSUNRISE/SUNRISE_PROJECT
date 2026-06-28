from app.services.prompt_title_service import generate_prompt_title


def test_generate_prompt_title_strips_leading_action_and_article():
    assert generate_prompt_title("create a simple wooden pipe") == "Simple Wooden Pipe"
    assert generate_prompt_title("Generate the metal desk lamp") == "Metal Desk Lamp"
    assert generate_prompt_title("write code for an oak table") == "Oak Table"


def test_generate_prompt_title_keeps_core_subject_under_limit():
    title = generate_prompt_title(
        "create a realistic high quality ornate wooden dining chair with curved arms"
    )

    assert title == "Ornate Wooden Chair"
    assert len(title) < 25


def test_generate_prompt_title_uses_title_case_and_fallback():
    assert generate_prompt_title("make a sci-fi door") == "Sci-Fi Door"
    assert generate_prompt_title("!!!") == "Untitled Prompt"
