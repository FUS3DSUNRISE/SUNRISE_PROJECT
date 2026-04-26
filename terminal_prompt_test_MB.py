import json
import time
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path


DEFAULT_BASE_URL = "http://127.0.0.1:5000"
DEFAULT_EMAIL = "terminal_mb@test.com"
DEFAULT_PASSWORD = "test123"
DEFAULT_CATEGORY = "Simple Objects"


def prompt_with_default(label, default):
    value = input(f"{label} [{default}]: ").strip()
    return value or default


def normalize_base_url(value):
    if not value.startswith(("http://", "https://")):
        print(f"'{value}' is not a backend URL. Using {DEFAULT_BASE_URL} instead.")
        return DEFAULT_BASE_URL
    return value.rstrip("/")


def request_json(opener, method, url, payload=None):
    data = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url=url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with opener.open(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8")
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {"raw": raw}
        return error.code, body
    except urllib.error.URLError as error:
        return 0, {
            "error": "Could not reach the backend API.",
            "details": str(error.reason),
            "hint": "Start Flask with: venv\\Scripts\\python.exe run.py",
        }


def authenticate(opener, base_url):
    print("\nAuthentication")
    email = prompt_with_default("Email", DEFAULT_EMAIL)
    password = prompt_with_default("Password", DEFAULT_PASSWORD)
    mode = prompt_with_default("Mode: login, signup, or auto", "auto").lower()

    payload = {"email": email, "password": password}

    if mode in {"login", "auto"}:
        status, body = request_json(opener, "POST", f"{base_url}/auth/login", payload)
        if status == 0:
            print(body["error"])
            print(body["hint"])
            print(f"Details: {body['details']}")
            return False
        if status == 200:
            print("Logged in successfully.")
            return True
        if mode == "login":
            print(f"Login failed ({status}): {body}")
            return False

    status, body = request_json(opener, "POST", f"{base_url}/auth/signup", payload)
    if status in {200, 201}:
        print("Signed up and logged in successfully.")
        return True

    raw_error = str(body.get("raw", "")) if isinstance(body, dict) else str(body)
    if "no such table: users" in raw_error:
        print("The backend is running, but the local database has not been initialized.")
        print("Stop Flask, then run this once from the project root:")
        print("venv\\Scripts\\python.exe create_db.py")
        print("Then restart Flask and run this MB script again.")
        print("Warning: create_db.py resets the local SQLite database.")
        return False

    print(f"Signup failed ({status}): {body}")
    return False


def print_ambiguity(ambiguity):
    if not ambiguity:
        print("Ambiguity metadata: missing")
        return

    print(f"Ambiguity detected: {ambiguity.get('detected')}")
    print(f"Primary case: {ambiguity.get('primary_case')}")

    followup = ambiguity.get("user_followup_message")
    if followup:
        print(f"LLM follow-up message: {followup}")

    cases = ambiguity.get("cases") or []
    if not cases:
        return

    print("Detected cases:")
    for case in cases:
        print(f"  - {case.get('name')}")
        print(f"    action: {case.get('recommended_action')}")
        print(f"    question: {case.get('clarification_question')}")
        print(f"    default: {case.get('default_resolution')}")


def result_local_path(result_path):
    if not result_path:
        return None

    repo_root = Path(__file__).resolve().parent
    relative_path = result_path.lstrip("/").replace("/", "\\")
    return repo_root / relative_path


def poll_generation(opener, base_url, prompt_id):
    print("\nPolling generation status...")

    while True:
        time.sleep(5)
        status, body = request_json(opener, "GET", f"{base_url}/prompts/{prompt_id}")

        if status != 200:
            print(f"Could not fetch prompt status ({status}): {body}")
            return

        current_status = body.get("status")
        print(f"Prompt {prompt_id}: {current_status}")

        if current_status not in {"queued", "processing"}:
            result_path = body.get("result_path")
            error_message = body.get("error_message")

            if current_status == "completed":
                print("Generation completed.")
                print(f"API result path: {result_path}")
                print(f"Local GLB path: {result_local_path(result_path)}")
            else:
                print("Generation did not complete successfully.")
                print(f"Error: {error_message}")
            return


def submit_prompt(opener, base_url, prompt_text, category):
    status, body = request_json(
        opener,
        "POST",
        f"{base_url}/prompts",
        {"prompt": prompt_text, "category": category},
    )

    print("\nAPI response")
    print(json.dumps(body, indent=2, ensure_ascii=False))

    raw_error = str(body.get("raw", "")) if isinstance(body, dict) else str(body)
    if "api_key client option must be set" in raw_error:
        print("\nThe backend reached the LLM step, but no API key is configured.")
        print("Create a .env file at the project root and add:")
        print("LLM_API_KEY=your_groq_key_here")
        print("Then restart Flask and Celery before running this script again.")
        return None

    if status != 201:
        print(f"Prompt was not queued. HTTP status: {status}")
        return None

    print("\nSummary")
    print(f"Prompt id: {body.get('id')}")
    print(f"Status: {body.get('status')}")
    print(f"Detected category: {body.get('category')}")
    print_ambiguity(body.get("ambiguity"))
    return body


def main():
    print("SUNRISE terminal prompt test - MB")
    print("This script is standalone. It only calls the local API.")
    print("Before using it, make sure Flask, Redis, Celery, and Blender are running.\n")

    base_url = normalize_base_url(prompt_with_default("Backend URL", DEFAULT_BASE_URL))
    cookie_jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

    if not authenticate(opener, base_url):
        return

    category = prompt_with_default("Category sent to backend", DEFAULT_CATEGORY)

    print("\nConversation mode")
    print("Type a prompt and press Enter.")
    print("Use the LLM follow-up message to write a refined prompt next.")
    print("Type 'quit' to stop.\n")

    while True:
        prompt_text = input("Prompt > ").strip()
        if prompt_text.lower() in {"quit", "exit", "q"}:
            print("Stopped.")
            return
        if not prompt_text:
            continue

        response = submit_prompt(opener, base_url, prompt_text, category)
        if not response:
            continue

        should_poll = prompt_with_default("Poll until 3D generation finishes? y/n", "y").lower()
        if should_poll == "y":
            poll_generation(opener, base_url, response["id"])

        print("\nYou can now enter a refined prompt, for example based on the follow-up message.\n")


if __name__ == "__main__":
    main()
