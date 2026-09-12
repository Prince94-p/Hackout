import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
from app.models.scenario import Scenario

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

import uuid

def test_phase6_simulator_preview_and_persistence():
    print("\n--- Running Phase 6 Simulator Tests ---")

    # 1. Register and setup demo factory
    u_id = uuid.uuid4().hex[:8]
    reg = client.post("/api/auth/register", json={
        "name": "Sim Engineer",
        "organization": "Carbon Sim Labs",
        "email": f"sim_eng_{u_id}@carboncore.local",
        "password": "Password123!"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    demo_res = client.post("/api/factories/demo", headers=headers)
    fid = demo_res.json()["id"]
    client.post(f"/api/factories/{fid}/calculate", headers=headers)

    # 2. Preview 100% implementation, 100% performance, 0% cost variation
    preview1 = client.post(f"/api/factories/{fid}/scenarios/preview", headers=headers, json={
        "recommendation_code": "compressor",
        "implementation_percent": 100.0,
        "performance_percent": 100.0,
        "cost_variation_percent": 0.0
    })
    assert preview1.status_code == 200, preview1.text
    p1 = preview1.json()
    assert p1["baseline_tco2e"] == 1150.0
    assert p1["effective_saving_tco2e"] == 74.0
    assert p1["future_footprint_tco2e"] == 1076.0
    assert p1["estimated_cost_inr_lakhs"] == 1.6
    print("✓ Full 100% preview calculation correct: 74 tCO₂e saving -> 1,076 tCO₂e footprint")

    # 3. Preview 50% scale, 90% performance, +20% cost variation
    # Multiplier saving = 0.5 * 0.9 = 0.45 -> 74 * 0.45 = 33.3
    # Cost = 1.6 * 0.5 * 1.2 = 0.96
    preview2 = client.post(f"/api/factories/{fid}/scenarios/preview", headers=headers, json={
        "recommendation_code": "compressor",
        "implementation_percent": 50.0,
        "performance_percent": 90.0,
        "cost_variation_percent": 20.0
    })
    assert preview2.status_code == 200
    p2 = preview2.json()
    assert p2["effective_saving_tco2e"] == 33.3
    assert p2["future_footprint_tco2e"] == round(1150.0 - 33.3, 1)
    assert p2["estimated_cost_inr_lakhs"] == 0.96
    print("✓ Partial scaling and sensitivity calculation verified: 33.3 tCO₂e saving, ₹0.96L cost")

    # 4. Confirm preview did NOT persist scenarios to DB
    list_before = client.get(f"/api/factories/{fid}/scenarios", headers=headers)
    assert list_before.status_code == 200
    assert len(list_before.json()) == 0
    print("✓ Sliders do NOT pollute database: 0 records persisted during preview")

    # 5. Explicitly Save Scenario (POST)
    save_res = client.post(f"/api/factories/{fid}/scenarios", headers=headers, json={
        "recommendation_code": "compressor",
        "implementation_percent": 75.0,
        "performance_percent": 95.0,
        "cost_variation_percent": 10.0,
        "title": "Staged Compressor Overhaul"
    })
    assert save_res.status_code == 201
    saved = save_res.json()
    assert saved["id"] is not None
    assert saved["title"] == "Staged Compressor Overhaul"
    # 75% * 95% = 0.7125 * 74 = 52.7
    assert saved["effective_saving_tco2e"] == 52.7
    assert saved["future_footprint_tco2e"] == round(1150.0 - 52.7, 1)
    print("✓ Explicit save correctly persists scenario to database with generated ID")

    # 6. Verify listing now returns 1 scenario
    list_after = client.get(f"/api/factories/{fid}/scenarios", headers=headers)
    assert len(list_after.json()) == 1

    print("--- Phase 6 All Tests Passed! ---\n")

if __name__ == "__main__":
    test_phase6_simulator_preview_and_persistence()
