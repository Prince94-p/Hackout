import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

import uuid

def test_phase7_roadmap_generation_and_custom_differentiation():
    print("\n--- Running Phase 7 Roadmap Tests ---")

    # 1. Register User & Demo Factory
    u_id = uuid.uuid4().hex[:8]
    reg = client.post("/api/auth/register", json={
        "name": "Roadmap Lead",
        "organization": "Decarb Strategies",
        "email": f"lead_{u_id}@decarbstrat.com",
        "password": "Password123!"
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    demo_res = client.post("/api/factories/demo", headers=headers)
    demo_fid = demo_res.json()["id"]
    client.post(f"/api/factories/{demo_fid}/calculate", headers=headers)

    # 2. Fetch Demo Roadmap
    rm_res = client.get(f"/api/factories/{demo_fid}/roadmap", headers=headers)
    assert rm_res.status_code == 200, rm_res.text
    demo_rm = rm_res.json()

    assert demo_rm["baseline_tco2e"] == 1150.0
    assert demo_rm["planned_saving_tco2e"] == 241.0
    assert demo_rm["target_footprint_tco2e"] == 909.0
    assert demo_rm["reduction_percent"] == 21.0
    assert demo_rm["total_cost_inr_lakhs"] == 10.6
    assert len(demo_rm["actions"]) == 3
    assert len(demo_rm["timeline_steps"]) == 5

    # Check action phases and details
    a1 = demo_rm["actions"][0]
    assert "Compressor" in a1["action_title"]
    assert a1["carbon_saving_tco2e"] == 74.0
    assert "0–3 Months" in a1["phase_label"]

    a2 = demo_rm["actions"][1]
    assert "Recycled Aluminium" in a2["action_title"]
    assert a2["carbon_saving_tco2e"] == 105.0
    assert "3–6 Months" in a2["phase_label"]

    a3 = demo_rm["actions"][2]
    assert "Waste Heat" in a3["action_title"]
    assert a3["carbon_saving_tco2e"] == 62.0
    assert "6–12 Months" in a3["phase_label"]

    # Check timeline progression
    tl = demo_rm["timeline_steps"]
    assert tl[0]["footprint_tco2e"] == 1150.0
    assert tl[1]["footprint_tco2e"] == 1076.0
    assert tl[2]["footprint_tco2e"] == 971.0
    assert tl[3]["footprint_tco2e"] == 909.0
    assert tl[4]["footprint_tco2e"] == 909.0
    print("✓ Demo factory roadmap validated: 1,150 -> 1,076 -> 971 -> 909 tCO₂e (241 tCO₂e total saving, ₹10.6L)")

    # 3. Create Custom Factory with Independent Data
    custom_fact = client.post("/api/factories", headers=headers, json={
        "name": "Precision Optics Facility",
        "industry": "Instruments",
        "location": "Chennai",
        "reporting_period": "2025",
        "annual_production": 25000.0,
        "production_unit": "units"
    })
    custom_fid = custom_fact.json()["id"]

    # Add custom activity: 200k kWh electricity, 5k kg material, 2k kg waste
    client.post(f"/api/factories/{custom_fid}/data", headers=headers, json={
        "energy_sources": [{"source_type": "Grid", "annual_consumption": 200000.0, "emission_factor": 0.5}],
        "material_inputs": [{"material_type": "Optical Glass", "annual_quantity": 5000.0, "emission_factor": 3.0}],
        "processes": [{"name": "Laser Cutting", "operating_hours": 2500.0, "annual_energy_kwh": 80000.0}],
        "waste_streams": [{"waste_type": "Glass Slag", "annual_quantity": 2000.0, "emission_factor": 1.0}]
    })
    # Baseline: 200k * 0.5 / 1000 = 100; Material: 5k * 3 / 1000 = 15; Waste: 2k * 1 / 1000 = 2 -> 117 tCO₂e
    client.post(f"/api/factories/{custom_fid}/calculate", headers=headers)

    custom_rm_res = client.get(f"/api/factories/{custom_fid}/roadmap", headers=headers)
    assert custom_rm_res.status_code == 200
    custom_rm = custom_rm_res.json()

    assert custom_rm["baseline_tco2e"] == 117.0
    assert custom_rm["baseline_tco2e"] != 1150.0, "Custom factory must not have demo baseline"
    assert custom_rm["planned_saving_tco2e"] != 241.0, "Custom factory must not have demo planned savings"
    assert custom_rm["planned_saving_tco2e"] > 0.0
    assert custom_rm["target_footprint_tco2e"] < 117.0
    assert len(custom_rm["actions"]) > 0
    print(f"✓ Custom factory roadmap dynamically derived from actual data: Baseline {custom_rm['baseline_tco2e']} tCO₂e, Planned saving {custom_rm['planned_saving_tco2e']} tCO₂e")

    # 4. Cross-user isolation check on roadmap
    u_id2 = uuid.uuid4().hex[:8]
    reg2 = client.post("/api/auth/register", json={
        "name": "Intruder",
        "organization": "Spy LLC",
        "email": f"intruder_{u_id2}@spy.com",
        "password": "Password123!"
    })
    token2 = reg2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    forbidden_res = client.get(f"/api/factories/{demo_fid}/roadmap", headers=headers2)
    assert forbidden_res.status_code == 403
    print("✓ User isolation verified: User B cannot view User A's factory roadmap")

    print("--- Phase 7 All Tests Passed! ---\n")

if __name__ == "__main__":
    test_phase7_roadmap_generation_and_custom_differentiation()
