import requests
import os
import time

BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")

SAMPLE_GOAL = "Plan a 5-day trip to Paris with sightseeing and food recommendations."


def test_plan_generation():
    print("Testing plan generation with Gemini API...")
    payload = {
        "goal": SAMPLE_GOAL,
        "start_date": "2025-09-22",
        "save_to_db": True
    }
    resp = requests.post(f"{BASE_URL}/plan", json=payload, timeout=10)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert data.get("success"), f"Plan generation failed: {data}"
    assert data.get("plan_data"), "No plan_data in response"
    assert isinstance(data["plan_data"], dict), "plan_data is not a dict"
    print("Plan generation: PASS")
    return data.get("plan_id")


def test_plan_saved(plan_id):
    print(f"Verifying plan saved to database (ID: {plan_id})...")
    resp = requests.get(f"{BASE_URL}/plans/{plan_id}", timeout=10)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert data.get("success"), f"Plan not found: {data}"
    assert data.get("plan_data", {}).get("goal") == SAMPLE_GOAL, "Saved plan goal mismatch"
    print("Plan save: PASS")


def test_invalid_api_key():
    print("Testing error handling for invalid Gemini API key...")
    # Temporarily override the Gemini API key
    orig_key = os.environ.get("GEMINI_API_KEY")
    os.environ["GEMINI_API_KEY"] = "INVALID_KEY"
    payload = {
        "goal": SAMPLE_GOAL,
        "start_date": "2025-09-22",
        "save_to_db": False
    }
    resp = requests.post(f"{BASE_URL}/plan", json=payload, timeout=10)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert not data.get("success"), "Expected failure with invalid API key"
    assert "API key" in data.get("message", ""), "Error message does not mention API key"
    print("Invalid API key error handling: PASS")
    # Restore original key
    if orig_key is not None:
        os.environ["GEMINI_API_KEY"] = orig_key
    else:
        del os.environ["GEMINI_API_KEY"]


def main():
    plan_id = test_plan_generation()
    time.sleep(1)  # Allow DB to commit
    test_plan_saved(plan_id)
    test_invalid_api_key()
    print("\nAll AI plan generation tests passed.")


if __name__ == "__main__":
    main()
