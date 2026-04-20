import requests
import time

BASE_URL = "http://localhost:5000/prompts"
SESSION_VALUE = "eyJ1c2VyX2lkIjoxfQ.aeZ5Mw.omSpjGVCIOARj2v0UB0KG1x8ROc"
COOKIES = {"session": SESSION_VALUE}

def run_integration_test():
    print(">>> STEP 1: Primary generation (LLM)...")
    initial_payload = {
        "prompt": "vintage wooden stool",
        "parameters": {
            "size": {"width": 1.0, "height": 1.0, "depth": 1.0},
            "geometry": {"complexity": 3, "smoothness": 10},
            "material": {"material_type": "Wood", "roughness": 0.8, "metallic": 0.0}
        }
    }
    
    res1 = requests.post(BASE_URL, json=initial_payload, cookies=COOKIES)
    
    if res1.status_code != 201:
        print(f"Creation error: {res1.status_code} - {res1.text}")
        return

    target_id = res1.json().get("id")
    print(f"Successfully created! Object ID: {target_id}")
    print("We wait 5 seconds for Blender to finish...")
    time.sleep(5) 

    print(f"\n>>> STEP 2: Fast Track Testing for ID {target_id}...")
    update_url = f"{BASE_URL}/{target_id}/update_params"
    
    fast_payload = {
        "parameters": {
            "size": {"width": 1.0, "height": 5.0, "depth": 1.0}, 
            "geometry": {"complexity": 3, "smoothness": 10},
            "material": {"material_type": "Wood", "roughness": 0.8, "metallic": 0.0}
        }
    }

    res2 = requests.post(update_url, json=fast_payload, cookies=COOKIES)

    if res2.status_code == 200:
        data = res2.json()
        print("SUCCESS! The server has accepted the update.")
        is_fast = data.get('fast_track')
        print(f"Whether Fast Track was used: {is_fast}")
        
        if is_fast:
            print("RESULT: The logic works correctly. AI is ignored, a replacement is used in the code.")
        else:
            print("ATTENTION: The server returned a status of 200, but Fast Track did not work (the prompt text may be different).")
    else:
        print(f"Fast Track Error: {res2.status_code} - {res2.text}")

if __name__ == "__main__":
    run_integration_test()