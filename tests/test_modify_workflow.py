import requests
import time

BASE_URL = "http://localhost:5000"
LOGIN_URL = f"{BASE_URL}/auth/login"   
PROMPTS_URL = f"{BASE_URL}/prompts"

EMAIL = "sarra@test.com"           
PASSWORD = "test123"                  

session = requests.Session()


def wait_until_done(prompt_id, timeout=180, interval=5):
    start = time.time()

    while time.time() - start < timeout:
        res = session.get(f"{PROMPTS_URL}/{prompt_id}")
        print(f"Polling prompt {prompt_id}: {res.status_code}")

        if res.status_code != 200:
            print("Polling error:", res.text)
            return None

        data = res.json()
        status = data.get("status")
        print("Current status:", status)

        if status == "completed":
            return data
        if status == "failed":
            return data

        time.sleep(interval)

    print("Timeout while waiting for prompt completion.")
    return None


def main():
    print(">>> STEP 0: LOGIN")
    login_payload = {
        "email": EMAIL,   
        "password": PASSWORD
    }

    login_res = session.post(LOGIN_URL, json=login_payload)
    print("LOGIN STATUS:", login_res.status_code)
    print("LOGIN RESPONSE:", login_res.text)

    if login_res.status_code != 200:
        print("Login failed. Stop.")
        return

    print("SESSION COOKIES:", session.cookies.get_dict())

    print("\n>>> STEP 1: CREATE BASE PROMPT")
    create_payload = {
        "prompt": "wooden stool",
        "parameters": {
            "size": {"width": 1.0, "height": 1.0, "depth": 1.0},
            "geometry": {"complexity": 3, "smoothness": 10},
            "material": {"material_type": "Wood", "roughness": 0.8, "metallic": 0.0}
        }
    }

    create_res = session.post(PROMPTS_URL, json=create_payload)
    print("CREATE STATUS:", create_res.status_code)
    print("CREATE RESPONSE:", create_res.text)

    if create_res.status_code != 201:
        print("Base prompt creation failed. Stop.")
        return

    base_id = create_res.json()["id"]
    print("BASE PROMPT ID:", base_id)

    base_result = wait_until_done(base_id)
    print("BASE RESULT:", base_result)

# parameters test

#    print("\n>>> STEP 2: TEST PARAMETERS ONLY")
#   params_only_payload = {
#       "parameters": {
#            "size": {"width": 1.0, "height": 2.0, "depth": 1.0},
#            "geometry": {"complexity": 3, "smoothness": 10},
#            "material": {"material_type": "Wood", "roughness": 0.8, "metallic": 0.0}
#        }
#    }

#    params_only_res = session.post(
#        f"{PROMPTS_URL}/{base_id}/update_params",
#        json=params_only_payload
#    )
#    print("PARAMETERS ONLY STATUS:", params_only_res.status_code)
#    print("PARAMETERS ONLY RESPONSE:", params_only_res.text)

#    if params_only_res.status_code == 200:
#        params_only_id = params_only_res.json()["id"]
#        print("PARAMETERS ONLY NEW ID:", params_only_id)
#        params_only_result = wait_until_done(params_only_id)
#        print("PARAMETERS ONLY FINAL RESULT:", params_only_result)

    print("\n>>> STEP 2 BIS: TEST PARAMETERS ONLY VIA MODIFY")

    params_only_modify_payload = {
        "parameters": {
            "size": {"width": 1.0, "height": 2.0, "depth": 1.0},
            "geometry": {"complexity": 3, "smoothness": 10},
            "material": {"material_type": "Wood", "roughness": 0.8, "metallic": 0.0}
        }
    }

    params_only_modify_res = session.post(
        f"{PROMPTS_URL}/{base_id}/modify",
        json=params_only_modify_payload
    )
    print("PARAMETERS ONLY VIA MODIFY STATUS:", params_only_modify_res.status_code)
    print("PARAMETERS ONLY VIA MODIFY RESPONSE:", params_only_modify_res.text)

    if params_only_modify_res.status_code == 201:
        params_only_modify_id = params_only_modify_res.json()["id"]
        print("PARAMETERS ONLY VIA MODIFY NEW ID:", params_only_modify_id)
        params_only_modify_result = wait_until_done(params_only_modify_id)
        print("PARAMETERS ONLY VIA MODIFY FINAL RESULT:", params_only_modify_result)

# command test
    print("\n>>> STEP 3: TEST COMMAND ONLY")
    command_only_payload = {
        "command": "make it twice as tall"
    }

    command_only_res = session.post(
        f"{PROMPTS_URL}/{base_id}/modify",
        json=command_only_payload
    )
    print("COMMAND ONLY STATUS:", command_only_res.status_code)
    print("COMMAND ONLY RESPONSE:", command_only_res.text)

    if command_only_res.status_code == 201:
        command_only_id = command_only_res.json()["id"]
        print("COMMAND ONLY NEW ID:", command_only_id)
        command_only_result = wait_until_done(command_only_id)
        print("COMMAND ONLY FINAL RESULT:", command_only_result)

# command and parameters test
    print("\n>>> STEP 4: TEST COMMAND + PARAMETERS")
    both_payload = {
        "command": "make it wooden and very tall",
        "parameters": {
            "size": {"width": 1.0, "height": 3.0, "depth": 1.0},
            "geometry": {"complexity": 5, "smoothness": 20},
            "material": {"material_type": "Metal", "roughness": 0.3, "metallic": 1.0}
        }
    }

    both_res = session.post(
        f"{PROMPTS_URL}/{base_id}/modify",
        json=both_payload
    )
    print("COMMAND + PARAMETERS STATUS:", both_res.status_code)
    print("COMMAND + PARAMETERS RESPONSE:", both_res.text)

    if both_res.status_code == 201:
        both_id = both_res.json()["id"]
        print("COMMAND + PARAMETERS NEW ID:", both_id)
        both_result = wait_until_done(both_id)
        print("COMMAND + PARAMETERS FINAL RESULT:", both_result)


if __name__ == "__main__":
    main()