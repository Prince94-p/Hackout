import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal, get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

def test_phase5_demo_recommendations():
    # 1. Register and login
    client.post("/api/auth/register", json={
        "name": "Phase 5 User",
        "organization": "Solutions Corp",
        "email": "sol_user@solutions.com",
        "password": "Password123!"
    })
    login_res = client.post("/api/auth/login", json={
        "email": "sol_user@solutions.com",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create demo factory
    demo_res = client.post("/api/factories/demo", headers=headers)
    assert demo_res.status_code == 200
    demo_fid = demo_res.json()["id"]

    # 3. Fetch recommendations for demo factory
    recs_res = client.get(f"/api/factories/{demo_fid}/recommendations", headers=headers)
    assert recs_res.status_code == 200
    recs = recs_res.json()
    assert len(recs) >= 3

    # Check top recommendation for demo: Compressor leak remediation
    comp_rec = next((r for r in recs if r["code"] == "compressor"), None)
    assert comp_rec is not None
    assert comp_rec["carbon_saving_tco2e"] == 74.0
    assert comp_rec["estimated_cost_inr_lakhs"] == 1.6
    assert comp_rec["payback_months"] == 3.4
    assert comp_rec["reduction_pct"] == 6.4
    assert comp_rec["confidence_pct"] == 88.0
    assert comp_rec["derivation_type"] == "calculated"
    assert comp_rec["assumption_reference"] is not None

    # Check single lookup
    single_res = client.get(f"/api/factories/{demo_fid}/recommendations/compressor", headers=headers)
    assert single_res.status_code == 200
    assert single_res.json()["title"] == comp_rec["title"]

def test_phase5_custom_factory_independent_recommendations():
    # Register another user
    client.post("/api/auth/register", json={
        "name": "Custom User",
        "organization": "Custom Mills",
        "email": "custom_sol@mills.com",
        "password": "Password123!"
    })
    login_res = client.post("/api/auth/login", json={
        "email": "custom_sol@mills.com",
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create custom factory
    fact_res = client.post("/api/factories", headers=headers, json={
        "name": "Heavy Stamping Unit",
        "industry": "Metal Stamping",
        "location": "Pune",
        "reporting_period": "2024-2025",
        "annual_production": 50000.0,
        "production_unit": "parts/year",
        "selected_processes": ["stamping", "heat-treatment"]
    })
    assert fact_res.status_code == 201, fact_res.text
    fid = fact_res.json()["id"]

    # Submit different data: high steel scrap, moderate diesel, low electricity
    client.post(f"/api/factories/{fid}/data", headers=headers, json={
        "energy_sources": [
            {
                "source_type": "Grid Electricity",
                "annual_consumption": 100000.0,
                "unit": "kWh/year",
                "emission_factor": 0.50,
                "factor_source": "State Grid CEA"
            }
        ],
        "material_inputs": [
            {
                "material_type": "Steel Billets",
                "annual_quantity": 50000.0,
                "unit": "kg/year",
                "recycled_content_percent": 10.0,
                "emission_factor": 2.2
            }
        ],
        "processes": [],
        "waste_streams": []
    })

    # Calculate baseline
    client.post(f"/api/factories/{fid}/calculate", headers=headers)

    # Fetch recommendations
    recs_res = client.get(f"/api/factories/{fid}/recommendations", headers=headers)
    assert recs_res.status_code == 200
    recs = recs_res.json()
    assert len(recs) > 0

    # Verify custom factory does NOT inherit the demo values
    comp_rec = next((r for r in recs if r["code"] == "compressor"), None)
    if comp_rec:
        assert comp_rec["carbon_saving_tco2e"] != 74.0
    
    top_rec = recs[0]
    assert top_rec["carbon_saving_tco2e"] > 0
    assert top_rec["assumption_reference"] is not None
    assert top_rec["confidence_pct"] > 0
