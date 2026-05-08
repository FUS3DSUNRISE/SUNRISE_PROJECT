import time
import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:5000"

LOGIN_DATA = {
    "email": "sarra@test.com",
    "password": "test123"
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALID_ASSET_PATH = PROJECT_ROOT / "static" / "models" / "prompt_1.glb"
INVALID_ASSET_PATH = PROJECT_ROOT / "tests" / "invalid_asset.txt"


def print_response(title, response):
    print(f"\n{title}: {response.status_code}")
    print(response.text)


def create_invalid_file():
    INVALID_ASSET_PATH.write_text("This is not a valid 3D asset.")


def wait_until_completed(session, prompt_id, timeout_seconds=180, interval_seconds=5):
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        response = session.get(f"{BASE_URL}/prompts/{prompt_id}")

        print(f"\nPOLL PROMPT {prompt_id}: {response.status_code}")
        print(response.text)

        if response.status_code != 200:
            raise Exception("Failed to get prompt status")

        data = response.json()
        status = data.get("status")

        if status == "completed":
            return data

        if status == "failed":
            raise Exception(f"Prompt failed: {data.get('error_message')}")

        time.sleep(interval_seconds)

    raise TimeoutError(f"Prompt {prompt_id} did not complete in time")


session = requests.Session()

login_response = session.post(
    f"{BASE_URL}/auth/login",
    json=LOGIN_DATA
)
print_response("LOGIN", login_response)

if login_response.status_code != 200:
    raise Exception("Login failed")


print("\nVALID ASSET PATH:", VALID_ASSET_PATH)
print("EXISTS:", VALID_ASSET_PATH.exists())

if not VALID_ASSET_PATH.exists():
    raise FileNotFoundError(f"Valid asset not found: {VALID_ASSET_PATH}")


with open(VALID_ASSET_PATH, "rb") as file:
    upload_response = session.post(
        f"{BASE_URL}/assets/import",
        files={"file": file}
    )

print_response("UPLOAD VALID FILE", upload_response)

if upload_response.status_code != 201:
    raise Exception("Valid asset upload failed")

asset_id = upload_response.json()["id"]


get_asset_response = session.get(f"{BASE_URL}/assets/{asset_id}")
print_response("GET UPLOADED ASSET BY ID", get_asset_response)

if get_asset_response.status_code != 200:
    raise Exception("Could not retrieve uploaded asset")

asset_data = get_asset_response.json()
metadata = asset_data.get("metadata")

print("\nMETADATA CHECK")
print("metadata exists:", metadata is not None)

if not metadata:
    raise Exception("Metadata should not be null for newly uploaded asset")

print("object_count:", metadata.get("object_count"))
print("objects:", metadata.get("objects"))
print("mesh_count:", metadata.get("mesh_count"))
print("meshes:", metadata.get("meshes"))
print("material_count:", metadata.get("material_count"))
print("materials:", metadata.get("materials"))


list_response = session.get(f"{BASE_URL}/assets/me")
print_response("GET MY ASSETS", list_response)

if list_response.status_code != 200:
    raise Exception("Could not list user assets")

my_assets = list_response.json().get("assets", [])
uploaded_asset_in_list = next(
    (asset for asset in my_assets if asset["id"] == asset_id),
    None
)

print("\nASSET LIST CHECK")
print("uploaded asset found in /assets/me:", uploaded_asset_in_list is not None)
print(
    "uploaded asset metadata exists:",
    uploaded_asset_in_list.get("metadata") is not None if uploaded_asset_in_list else False
)

if uploaded_asset_in_list is None:
    raise Exception("Uploaded asset not found in /assets/me")


modify_response = session.post(
    f"{BASE_URL}/assets/{asset_id}/modify",
    json={
        "command": "Change the chair material to wood"
    }
)

print_response("MODIFY IMPORTED ASSET", modify_response)

if modify_response.status_code != 201:
    raise Exception("Imported asset modification request failed")

prompt_id = modify_response.json()["id"]

completed_prompt = wait_until_completed(
    session=session,
    prompt_id=prompt_id,
    timeout_seconds=180,
    interval_seconds=5
)

print("\nFINAL PROMPT STATUS CHECK")
print("prompt_id:", completed_prompt.get("id"))
print("status:", completed_prompt.get("status"))
print("result_path:", completed_prompt.get("result_path"))

if completed_prompt.get("status") != "completed":
    raise Exception("Prompt should be completed")

if not completed_prompt.get("result_path"):
    raise Exception("Completed prompt should have a result_path")


file_response = session.get(f"{BASE_URL}/prompts/{prompt_id}/file")

print("\nGET MODIFIED GLB FILE:", file_response.status_code)

if file_response.status_code != 200:
    raise Exception("Modified GLB file should be accessible")

print("Modified GLB file is accessible.")


create_invalid_file()

with open(INVALID_ASSET_PATH, "rb") as file:
    invalid_response = session.post(
        f"{BASE_URL}/assets/import",
        files={"file": file}
    )

print_response("UPLOAD INVALID FILE", invalid_response)

if invalid_response.status_code == 400:
    print("\nInvalid file correctly rejected.")
else:
    raise Exception("Invalid file should have been rejected")


print("\nUS20 + US21 BACKEND TEST PASSED")