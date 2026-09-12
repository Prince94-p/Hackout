import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, Base

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_phase_2():
    print("\n--- Running Phase 2 Tests ---")
    # 1. Register User
    res = client.post("/api/auth/register", json={
        "name": "Test Engineer",
        "organization": "Modern Dynamics",
        "email": "engineer@moderndynamics.com",
        "password": "SecurePassword123!"
    })
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Real Factory
    res_f = client.post("/api/factories", headers=headers, json={
        "name": "Custom Precision Hub",
        "industry": "Machinery",
        "location": "Pune, Maharashtra",
        "reporting_period": "FY 2024-2025",
        "annual_production": 80000.0,
        "production_unit": "parts/year"
    })
    factory_id = res_f.json()["id"]

    # 3. Post Custom Activity Data
    payload = {
        "energy_sources": [
            {
                "source_type": "Grid Electricity",
                "annual_consumption": 500000.0,
                "unit": "kWh/year",
                "emission_factor": 0.50,
                "factor_source": "State Grid CEA"
            }
        ],
        "material_inputs": [
            {
                "material_type": "Steel Billets",
                "annual_quantity": 20000.0,
                "unit": "kg/year",
                "recycled_content_percent": 30.0,
                "emission_factor": 5.0
            }
        ],
        "processes": [
            {
                "name": "Milling Line",
                "equipment": "4 × Milling Machines",
                "operating_hours": 4000.0,
                "primary_energy_source": "Grid Electricity",
                "operating_pressure_bar": 0.0,
                "estimated_leakage_percent": 0.0,
                "annual_energy_kwh": 200000.0,
                "notes": "Milling line electricity included in factory grid power"
            }
        ],
        "waste_streams": [
            {
                "waste_type": "Steel Scrap",
                "annual_quantity": 10000.0,
                "unit": "kg/year",
                "treatment_method": "Recycling Partner",
                "emission_factor": 1.5
            }
        ]
    }
    res_data = client.post(f"/api/factories/{factory_id}/data", headers=headers, json=payload)
    assert res_data.status_code == 200
    assert len(res_data.json()["energy_sources"]) == 1
    print("✓ Custom activity data saved")

    # 4. Calculate Baseline
    res_calc = client.post(f"/api/factories/{factory_id}/calculate", headers=headers)
    assert res_calc.status_code == 200
    calc = res_calc.json()

    # Deterministic checks:
    # Energy: 500000 * 0.5 / 1000 = 250.0
    # Material: 20000 * 5.0 / 1000 = 100.0
    # Waste: 10000 * 1.5 / 1000 = 15.0
    # Total: 365.0
    assert calc["energy_tco2e"] == 250.0, f"Expected 250, got {calc['energy_tco2e']}"
    assert calc["material_tco2e"] == 100.0, f"Expected 100, got {calc['material_tco2e']}"
    assert calc["waste_tco2e"] == 15.0, f"Expected 15, got {calc['waste_tco2e']}"
    assert calc["total_tco2e"] == 365.0, f"Expected 365, got {calc['total_tco2e']}"
    assert calc["largest_source"] == "Energy"
    print("✓ Deterministic baseline calculation correct (365.0 tCO₂e)")
    print(f"✓ Explainable confidence: {calc['confidence']}% with breakdown: {calc['confidence_breakdown']}")
    assert len(calc["factor_traceability"]) == 3
    print("✓ Factor traceability confirmed")

    # 5. Check Demo Factory Baseline
    res_demo = client.post("/api/factories/demo", headers=headers)
    demo_id = res_demo.json()["id"]
    res_demo_calc = client.post(f"/api/factories/{demo_id}/calculate", headers=headers)
    dcalc = res_demo_calc.json()
    assert dcalc["energy_tco2e"] == 600.0
    assert dcalc["material_tco2e"] == 400.0
    assert dcalc["waste_tco2e"] == 150.0
    assert dcalc["total_tco2e"] == 1150.0
    print("✓ Demo Factory baseline matches verified demo values (600 + 400 + 150 = 1,150 tCO₂e)")

    print("--- Phase 2 All Tests Passed! ---\n")

if __name__ == "__main__":
    test_phase_2()
