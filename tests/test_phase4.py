import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_phase_4():
    print("\n--- Running Phase 4 Tests ---")
    res_reg = client.post("/api/auth/register", json={
        "name": "Reliability Lead",
        "organization": "AeroForge",
        "email": "lead@aeroforge.com",
        "password": "Password123!"
    })
    token = res_reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Custom factory with NO compressed air
    res_f = client.post("/api/factories", headers=headers, json={
        "name": "Heavy Stamping Works",
        "industry": "Forging",
        "location": "Jamshedpur",
        "reporting_period": "2025",
        "annual_production": 40000.0,
        "production_unit": "parts"
    })
    f_id = res_f.json()["id"]

    client.post(f"/api/factories/{f_id}/data", headers=headers, json={
        "energy_sources": [{"source_type": "Grid", "annual_consumption": 800000.0, "emission_factor": 0.5}],
        "material_inputs": [{"material_type": "Titanium Bars", "annual_quantity": 15000.0, "emission_factor": 12.0}],
        "processes": [{"name": "Heavy Hydraulic Press", "equipment": "3000T Press", "operating_hours": 5000.0, "annual_energy_kwh": 500000.0}],
        "waste_streams": [{"waste_type": "Scale", "annual_quantity": 2000.0, "emission_factor": 0.8}]
    })
    client.post(f"/api/factories/{f_id}/calculate", headers=headers)

    # Fetch hotspots for custom factory
    res_hotspots = client.get(f"/api/factories/{f_id}/hotspots", headers=headers)
    assert res_hotspots.status_code == 200
    h_list = res_hotspots.json()
    assert len(h_list) > 0
    # Must NOT force compressed air
    codes = [h["code"] for h in h_list]
    assert "compressed-air" not in codes, "Custom factory without compressed air should not have compressed-air hotspot"
    print(f"✓ Custom factory correctly diagnosed without forcing compressed air. Top hotspot: {h_list[0]['title']}")

    # 2. Demo Factory Hotspots & Root Cause
    res_demo = client.post("/api/factories/demo", headers=headers)
    demo_id = res_demo.json()["id"]
    client.post(f"/api/factories/{demo_id}/calculate", headers=headers)

    res_d_hotspots = client.get(f"/api/factories/{demo_id}/hotspots", headers=headers)
    assert res_d_hotspots.status_code == 200
    d_list = res_d_hotspots.json()
    d_codes = [h["code"] for h in d_list]
    assert "compressed-air" in d_codes
    assert "cnc" in d_codes
    assert "aluminium" in d_codes
    print("✓ Demo factory correctly identifies compressed-air, cnc, and aluminium hotspots")

    # 3. Root cause diagnosis for Demo compressed air
    res_rc = client.get(f"/api/factories/{demo_id}/root-cause?hotspot_code=compressed-air", headers=headers)
    assert res_rc.status_code == 200
    rc = res_rc.json()
    assert "leakage" in rc["root_cause_label"].lower() or "over-pressurization" in rc["root_cause_label"].lower()
    assert len(rc["evidence_points"]) >= 2
    assert len(rc["assumptions"]) >= 1
    assert rc["leakage_metric"] == "28%"
    assert rc["pressure_metric"] == "7.5 bar"
    print("✓ Transparent root-cause diagnosis returned with concrete evidence and assumptions")

    print("--- Phase 4 All Tests Passed! ---\n")

if __name__ == "__main__":
    test_phase_4()
