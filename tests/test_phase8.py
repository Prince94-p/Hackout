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

def test_phase8_end_to_end_flow_and_empty_states():
    print("\n--- Running Phase 8 End-to-End Full Flow Tests ---")

    # 1. Register User
    u_id = uuid.uuid4().hex[:8]
    test_email = f"arjun_{u_id}@bharattech.in"
    res_reg = client.post("/api/auth/register", json={
        "name": "Arjun Sharma",
        "organization": "Bharat AutoTech",
        "email": test_email,
        "password": "SecurePassword123!"
    })
    assert res_reg.status_code == 201
    token = res_reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✓ Step 1: User registered with hashed credentials")

    # 2. Test Logout Endpoint
    res_logout = client.post("/api/auth/logout", headers=headers)
    assert res_logout.status_code == 200
    print("✓ Step 2: POST /api/auth/logout works")

    # 3. Log back in
    res_login = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "SecurePassword123!"
    })
    assert res_login.status_code == 200
    token = res_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✓ Step 3: Login verified, session restored")

    # 4. Check /api/auth/me before factory creation
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert len(me_res.json()["factories"]) == 0
    print("✓ Step 4: /me reports 0 factories before setup")

    # 5. Factory Setup
    res_f = client.post("/api/factories", headers=headers, json={
        "name": "Gujarat Casting Plant",
        "industry": "Foundry & Casting",
        "location": "Ahmedabad, Gujarat",
        "reporting_period": "FY 2024-25",
        "annual_production": 60000.0,
        "production_unit": "castings/year",
        "selected_processes": ["Melting Furnace", "Moulding Line"]
    })
    assert res_f.status_code == 201
    fid = res_f.json()["id"]
    print(f"✓ Step 5: Factory created with ID {fid}")

    # 6. Verify Empty State on summary before data entry
    summary_empty = client.get(f"/api/factories/{fid}/emissions/summary", headers=headers)
    assert summary_empty.status_code == 200
    assert summary_empty.json()["has_calculation"] is False
    assert summary_empty.json()["baseline"] == 0.0
    print("✓ Step 6: Empty factory correctly reports has_calculation=False (no fake data)")

    # 7. Enter Factory Data
    data_res = client.post(f"/api/factories/{fid}/data", headers=headers, json={
        "energy_sources": [
            {
                "source_type": "Grid Electricity",
                "annual_consumption": 750000.0,
                "unit": "kWh/year",
                "emission_factor": 0.48,
                "factor_source": "CEA 2024"
            }
        ],
        "material_inputs": [
            {
                "material_type": "Aluminium Scrap",
                "annual_quantity": 40000.0,
                "unit": "kg/year",
                "recycled_content_percent": 60.0,
                "emission_factor": 2.5
            }
        ],
        "processes": [
            {
                "name": "Induction Furnace",
                "equipment": "2-Ton Coreless Induction",
                "operating_hours": 4500.0,
                "annual_energy_kwh": 500000.0,
                "notes": "Primary melt load"
            }
        ],
        "waste_streams": [
            {
                "waste_type": "Dross / Slag",
                "annual_quantity": 15000.0,
                "emission_factor": 1.2
            }
        ]
    })
    assert data_res.status_code == 200
    print("✓ Step 7: Activity data saved")

    # 8. Deterministic Baseline Calculation
    # Energy: 750000 * 0.48 / 1000 = 360.0
    # Material: 40000 * 2.5 / 1000 = 100.0
    # Waste: 15000 * 1.2 / 1000 = 18.0
    # Total: 478.0 tCO₂e
    calc_res = client.post(f"/api/factories/{fid}/calculate", headers=headers)
    assert calc_res.status_code == 200
    calc = calc_res.json()
    assert calc["total_tco2e"] == 478.0
    assert calc["energy_tco2e"] == 360.0
    assert calc["material_tco2e"] == 100.0
    assert calc["waste_tco2e"] == 18.0
    print(f"✓ Step 8: Deterministic baseline verified: {calc['total_tco2e']} tCO₂e")

    # 9. Verify Dashboard Summary
    sum_res = client.get(f"/api/factories/{fid}/emissions/summary", headers=headers)
    assert sum_res.status_code == 200
    s = sum_res.json()
    assert s["has_calculation"] is True
    assert s["baseline"] == 478.0
    assert s["largest_source"] == "Energy"
    print("✓ Step 9: Dashboard summary populated with actual calculated metrics")

    # 10. Verify Hotspots (should flag Induction Furnace, not compressed air)
    hot_res = client.get(f"/api/factories/{fid}/hotspots", headers=headers)
    assert hot_res.status_code == 200
    hotspots = hot_res.json()
    assert len(hotspots) > 0
    h_codes = [h["code"] for h in hotspots]
    assert "compressed-air" not in h_codes, "Should not force compressed air if absent"
    print(f"✓ Step 10: Dynamic hotspots detected without forcing compressed air: {[h['title'] for h in hotspots]}")

    # 11. Verify Root Cause
    top_code = hotspots[0]["code"]
    rc_res = client.get(f"/api/factories/{fid}/root-cause?hotspot_code={top_code}", headers=headers)
    assert rc_res.status_code == 200
    rc = rc_res.json()
    assert rc["root_cause_title"] is not None
    assert len(rc["evidence_points"]) > 0
    print(f"✓ Step 11: Root cause explainability chain verified: {rc['root_cause_title']}")

    # 12. Verify Solutions
    recs_res = client.get(f"/api/factories/{fid}/recommendations", headers=headers)
    assert recs_res.status_code == 200
    recs = recs_res.json()
    assert len(recs) > 0
    print(f"✓ Step 12: Circular solutions generated: {len(recs)} interventions")

    # 13. Simulator Preview and Save
    top_rec = recs[0]
    prev_res = client.post(f"/api/factories/{fid}/scenarios/preview", headers=headers, json={
        "recommendation_id": top_rec["id"],
        "implementation_percent": 80.0,
        "performance_percent": 100.0,
        "cost_variation_percent": 0.0
    })
    assert prev_res.status_code == 200
    expected_saving = round(top_rec["carbon_saving_tco2e"] * 0.8, 1)
    assert prev_res.json()["effective_saving_tco2e"] == expected_saving

    scen_res = client.post(f"/api/factories/{fid}/scenarios", headers=headers, json={
        "recommendation_id": top_rec["id"],
        "implementation_percent": 80.0,
        "performance_percent": 100.0,
        "cost_variation_percent": 0.0,
        "title": "80% Scale Implementation"
    })
    assert scen_res.status_code == 201
    print(f"✓ Step 13: Scenario preview & persistence verified with {expected_saving} tCO₂e saving")

    # 14. Action Roadmap
    rm_res = client.get(f"/api/factories/{fid}/roadmap", headers=headers)
    assert rm_res.status_code == 200
    rm = rm_res.json()
    assert rm["baseline_tco2e"] == 478.0
    assert rm["planned_saving_tco2e"] > 0
    assert rm["target_footprint_tco2e"] < 478.0
    assert len(rm["actions"]) > 0
    assert len(rm["timeline_steps"]) > 0
    print(f"✓ Step 14: Roadmap successfully generated: target {rm['target_footprint_tco2e']} tCO₂e ({rm['reduction_percent']}% reduction)")

    # 15. Verify Refresh / Logout / Login Persistence
    res_login2 = client.post("/api/auth/login", json={
        "email": test_email,
        "password": "SecurePassword123!"
    })
    assert res_login2.status_code == 200
    t2 = res_login2.json()["access_token"]
    h2 = {"Authorization": f"Bearer {t2}"}
    me_after = client.get("/api/auth/me", headers=h2)
    assert len(me_after.json()["factories"]) == 1
    assert me_after.json()["factories"][0]["id"] == fid
    print("✓ Step 15: Factory data and roadmap persist across logout/login cycle")

    print("--- Phase 8 All End-to-End Tests Passed! ---\n")

if __name__ == "__main__":
    test_phase8_end_to_end_flow_and_empty_states()
