import requests

BASE_URL = "https://task-planner-agent-ejj8.onrender.com"

def check_health():
    r = requests.get(f"{BASE_URL}/health", timeout=10)
    print("Health endpoint:", r.status_code, r.text)
    try:
        data = r.json()
    except Exception as e:
        print("Health endpoint did not return valid JSON:", e)
        return False, None
    if r.status_code != 200 or data.get("status") not in ("healthy", "degraded"):
        print("Health check failed:", data)
        return False, data
    return True, data

def create_plan():
    payload = {
        "goal": "Test product launch",
        "start_date": "2025-10-01",
        "save_to_db": True
    }
    r = requests.post(f"{BASE_URL}/plan", json=payload, timeout=10)
    print("Create Plan:", r.status_code, r.text)
    try:
        data = r.json()
    except Exception as e:
        print("Create plan did not return valid JSON:", e)
        return False, None
    if r.status_code != 200 or not data.get("success"):
        print("Plan creation failed:", data)
        return False, data
    return True, data

def get_plans():
    r = requests.get(f"{BASE_URL}/plans", timeout=10)
    print("Get Plans:", r.status_code, r.text)
    try:
        data = r.json()
    except Exception as e:
        print("Get plans did not return valid JSON:", e)
        return False, None
    if r.status_code != 200 or not data.get("success"):
        print("Get plans failed:", data)
        return False, data
    return True, data

def get_plan_by_id(plan_id):
    r = requests.get(f"{BASE_URL}/plans/{plan_id}", timeout=10)
    print(f"Get Plan {plan_id}:", r.status_code, r.text)
    try:
        data = r.json()
    except Exception as e:
        print(f"Get plan by id did not return valid JSON: {e}")
        return False, None
    if r.status_code != 200 or not data.get("success"):
        print(f"Get plan by id failed: {data}")
        return False, data
    return True, data

if __name__ == "__main__":
    print("--- Running Render Deployment Status Check ---")
    ok, health = check_health()
    if not ok:
        print("[FAIL] Health endpoint failed. Check database connection and environment variables.")
        exit(1)
    ok, plan = create_plan()
    if not ok:
        print("[FAIL] Plan creation failed. Check /plan endpoint, AI agent, and logs.")
        exit(1)
    plan_id = plan.get("plan_id")
    ok, plans = get_plans()
    if not ok:
        print("[FAIL] Get plans failed. Check /plans endpoint and database persistence.")
        exit(1)
    if not plan_id:
        print("[FAIL] No plan_id returned from plan creation. Check /plan endpoint logic.")
        exit(1)
    ok, plan_detail = get_plan_by_id(plan_id)
    if not ok:
        print(f"[FAIL] Get plan by id failed for id {plan_id}. Check /plans/{{id}} endpoint and database.")
        exit(1)
    print("\n[SUCCESS] All checks passed. Your Render deployment is production-ready!")
