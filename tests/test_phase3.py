import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_phase_3():
    print("\n--- Running Phase 3 Tests ---")
    res_reg = client.post("/api/auth/register", json={
        "name": "Audit Lead",
        "organization": "Clean Industrial",
        "email": "audit@clean.com",
        "password": "Password123!"
    })
    token = res_reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. New factory without calculation
    res_f = client.post("/api/factories", headers=headers, json={
        "name": "Fresh Green Plant",
        "industry": "Electronics",
        "location": "Bengaluru",
        "reporting_period": "2025",
        "annual_production": 10000.0,
        "production_unit": "units"
    })
    f_id = res_f.json()["id"]

    # Summary must have has_calculation=False
    res_s1 = client.get(f"/api/factories/{f_id}/emissions/summary", headers=headers)
    assert res_s1.status_code == 200
    s1 = res_s1.json()
    assert s1["has_calculation"] is False
    assert s1["baseline"] == 0.0
    print("✓ Empty factory reports has_calculation=False for proper empty-state display")

    # 2. Add custom activity and calculate
    payload = {
        "energy_sources": [{"source_type": "Grid", "annual_consumption": 300000.0, "emission_factor": 0.5}],
        "material_inputs": [{"material_type": "Copper", "annual_quantity": 10000.0, "emission_factor": 4.0}],
        "processes": [{"name": "Assembly", "operating_hours": 3000.0, "annual_energy_kwh": 100000.0}],
        "waste_streams": [{"waste_type": "General", "annual_quantity": 5000.0, "emission_factor": 1.0}]
    }
    client.post(f"/api/factories/{f_id}/data", headers=headers, json=payload)
    client.post(f"/api/factories/{f_id}/calculate", headers=headers)

    res_s2 = client.get(f"/api/factories/{f_id}/emissions/summary", headers=headers)
    assert res_s2.status_code == 200
    s2 = res_s2.json()
    assert s2["has_calculation"] is True
    # Energy = 300000 * 0.5 / 1000 = 150
    # Materials = 10000 * 4.0 / 1000 = 40
    # Waste = 5000 * 1.0 / 1000 = 5
    # Total = 195
    assert s2["baseline"] == 195.0
    assert s2["energy_tco2e"] == 150.0
    assert s2["material_tco2e"] == 40.0
    assert s2["waste_tco2e"] == 5.0
    assert s2["largest_source"] == "Energy"
    assert len(s2["source_distribution"]) == 3
    print("✓ Custom factory summary has exact calculated metrics (195 tCO₂e) and custom distribution")

    # 3. Demo Factory check
    res_demo = client.post("/api/factories/demo", headers=headers)
    demo_id = res_demo.json()["id"]
    client.post(f"/api/factories/{demo_id}/calculate", headers=headers)
    res_demo_sum = client.get(f"/api/factories/{demo_id}/emissions/summary", headers=headers)
    dsum = res_demo_sum.json()
    assert dsum["has_calculation"] is True
    assert dsum["baseline"] == 1150.0
    assert dsum["energy_tco2e"] == 600.0
    assert dsum["material_tco2e"] == 400.0
    assert dsum["waste_tco2e"] == 150.0
    assert "Compressed Air" in dsum["priority_leak"]
    assert dsum["wasted_kwh"] == 94500.0
    assert dsum["priority_footprint"] == 162.0
    print("✓ Demo factory summary correctly provides verified demo metrics (1,150 tCO₂e, 94.5k kWh wasted, 162 tCO₂e)")

    print("--- Phase 3 All Tests Passed! ---\n")

if __name__ == "__main__":
    test_phase_3()
