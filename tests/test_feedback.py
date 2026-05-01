import requests

BASE_URL = "http://127.0.0.1:5000"
session = requests.Session()


def show_response(name, response):
    print(f"\n--- {name} ---")
    print("STATUS:", response.status_code)
    print("TEXT:", response.text[:1000])

    try:
        return response.json()
    except requests.exceptions.JSONDecodeError:
        print("Response is not JSON.")
        return None


# 1. Signup ou login
user_data = {
    "email": "sarra@test.com",
    "password": "test123"
}

response = session.post(f"{BASE_URL}/auth/signup", json=user_data)
data = show_response("SIGNUP", response)

if response.status_code == 409:
    response = session.post(f"{BASE_URL}/auth/login", json=user_data)
    data = show_response("LOGIN", response)


# 2. Tester avec un prompt déjà existant
prompt_id = 1

feedback_data = {
    "rating": "positive",
    "accuracy_score": 4,
    "quality_score": 5,
    "comment": "The generated asset matches the prompt well."
}

response = session.post(
    f"{BASE_URL}/prompts/{prompt_id}/feedback",
    json=feedback_data
)
show_response("CREATE FEEDBACK", response)


# 3. Analytics
response = session.get(f"{BASE_URL}/prompts/feedback/analytics")
show_response("ANALYTICS", response)


# 4. Export CSV
response = session.get(f"{BASE_URL}/prompts/feedback/export")
show_response("EXPORT CSV", response)