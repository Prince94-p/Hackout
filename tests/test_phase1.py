import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base

# Reset test db
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_phase_1():
    print("\n--- Running Phase 1 Tests ---")
    # 1. Register User A
    res = client.post("/api/auth/register", json={
        "name": "Prince Patel",
        "organization": "GreenTech Ltd",
        "email": "prince@greentech.com",
        "password": "Password123!"
    })
    assert res.status_code == 201, f"Register failed: {res.text}"
    token_a = res.json()["access_token"]
    user_a_id = res.json()["user"]["id"]
    print("✓ User A registered successfully")

    # 2. Duplicate registration fails
    res_dup = client.post("/api/auth/register", json={
        "name": "Prince Patel",
        "organization": "GreenTech Ltd",
        "email": "prince@greentech.com",
        "password": "Password123!"
    })
    assert res_dup.status_code == 400
    print("✓ Duplicate email prevented")

    # 3. Login User A
    res_login = client.post("/api/auth/login", json={
        "email": "prince@greentech.com",
        "password": "Password123!"
    })
    assert res_login.status_code == 200
    assert res_login.json()["has_factory"] is False
    print("✓ User A login successful, has_factory=False")

    # 4. Create Factory for User A
    headers_a = {"Authorization": f"Bearer {token_a}"}
    res_fact = client.post("/api/factories", headers=headers_a, json={
        "name": "Gujarat Precision Works",
        "industry": "Automotive Tier 1",
        "location": "Sanand, Gujarat",
        "reporting_period": "FY 2024-2025",
        "annual_production": 50000.0,
        "production_unit": "parts/year",
        "selected_processes": ["CNC Machining", "Compressed Air"]
    })
    assert res_fact.status_code == 201
    factory_a_id = res_fact.json()["id"]
    assert res_fact.json()["is_demo"] is False
    print("✓ Factory created for User A (is_demo=False)")

    # 5. Register User B
    res_b = client.post("/api/auth/register", json={
        "name": "Other User",
        "organization": "Competitor Corp",
        "email": "other@competitor.com",
        "password": "Password456!"
    })
    assert res_b.status_code == 201
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 6. User B attempts to access User A's factory -> Forbidden 403
    res_forbidden = client.get(f"/api/factories/{factory_a_id}", headers=headers_b)
    assert res_forbidden.status_code == 403, f"Expected 403, got {res_forbidden.status_code}"
    print("✓ Cross-user isolation verified: User B cannot access User A's factory")

    # 7. Create Demo Factory for User A
    res_demo = client.post("/api/factories/demo", headers=headers_a)
    assert res_demo.status_code == 200
    assert res_demo.json()["is_demo"] is True
    assert res_demo.json()["name"] == "Apex Components Pvt. Ltd."
    print("✓ Demo factory created with is_demo=True and verified inputs")

    print("--- Phase 1 All Tests Passed! ---\n")

if __name__ == "__main__":
    test_phase_1()
