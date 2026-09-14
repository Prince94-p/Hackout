"""Original QA fixtures and failure reproductions; use run_postgres.py for races."""
import copy
import uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

@pytest.fixture
def owner():
    email = f'qa-{uuid.uuid4().hex}@example.com'
    response = client.post('/api/auth/register', json=dict(name='QA Owner', organization='QA Factory', email=email, password='ValidPassword123!'))
    assert response.status_code == 201, response.text
    return {'Authorization': 'Bearer ' + response.json()['access_token']}, email

@pytest.fixture
def factory(owner):
    headers, _ = owner
    payload = dict(name='QA Factory', industry='Manufacturing', location='Pune', reporting_period='2026', annual_production=1000, production_unit='units/year', selected_processes=['Packaging', 'Custom process'])
    response = client.post('/api/factories', headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return headers, response.json()['id']

def activity(energy=311000, material=700000, waste=35000, ef=.48, mf=.7, wf=.5):
    return dict(energy_sources=[dict(source_type='Grid Electricity', annual_consumption=energy, emission_factor=ef, factor_source='QA custom factor')], material_inputs=[dict(material_type='Production material', annual_quantity=material, emission_factor=mf, recycled_content_percent=10)], processes=[], waste_streams=[dict(waste_type='Production waste', annual_quantity=waste, emission_factor=wf, treatment_method='External Recycling')])

def populated(factory):
    headers, fid = factory
    response = client.post(f'/api/factories/{fid}/data', headers=headers, json=activity())
    assert response.status_code == 200, response.text
    return headers, fid

@pytest.mark.parametrize('payload', [dict(name='',organization='',email='qa-invalid-20260913-1757',password='x'),dict(name=' ',organization='X',email='a@example.com',password='longpassword'),dict(name='X',organization='X',email='a@example.com trailing',password='longpassword'),dict(name='X',organization='X',email='a@example.com',password='x'*73)])
def test_invalid_registration(payload):
    assert client.post('/api/auth/register',json=payload).status_code == 422

def test_login_logout_replay(owner):
    headers,email=owner
    assert client.post('/api/auth/login',json={'email':email,'password':'wrong'}).status_code==401
    assert client.post('/api/auth/logout',headers=headers).status_code==200
    assert client.get('/api/auth/me',headers=headers).status_code==401
    login=client.post('/api/auth/login',json={'email':email,'password':'ValidPassword123!'})
    assert login.status_code==200
    assert client.get('/api/auth/me',headers={'Authorization':'Bearer '+login.json()['access_token']}).status_code==200

@pytest.mark.parametrize('values,expected', [((1250000,50000,12500,.48,8,2),1025),((420000,100000,8000,.5,5,1.5),722),((850000,1500000,45000,.202,.12,.08),355.3),((310000,700000,35000,.48,.7,.5),656.3),((560000,250000,18000,.48,2.5,1.2),915.4)])
def test_original_baselines(factory,values,expected):
    h,f=factory
    r=client.post(f'/api/factories/{f}/data',headers=h,json=activity(*values));assert r.status_code==200,r.text
    summary=client.get(f'/api/factories/{f}/emissions/summary',headers=h);assert summary.status_code==200,summary.text
    assert summary.json()['baseline']==expected
    for endpoint in ['hotspots','recommendations','roadmap']:
        result=client.get(f'/api/factories/{f}/{endpoint}',headers=h);assert result.status_code==200,result.text

@pytest.mark.parametrize('category,field,value',[('energy_sources','annual_consumption',-100),('material_inputs','recycled_content_percent',150),('waste_streams','annual_quantity',-10),('energy_sources','emission_factor',-1)])
def test_invalid_activity(factory,category,field,value):
    h,f=factory;p=activity();p[category][0][field]=value
    assert client.post(f'/api/factories/{f}/data',headers=h,json=p).status_code==422

def test_empty_and_inconsistent(factory):
    h,f=factory
    assert client.get(f'/api/factories/{f}/emissions/summary',headers=h).json()['has_calculation'] is False
    assert client.post(f'/api/factories/{f}/data',headers=h,json={}).status_code==422
    p=activity();p['processes']=[dict(name='Compressor',annual_energy_kwh=999999,primary_energy_source='Grid Electricity')]
    assert client.post(f'/api/factories/{f}/data',headers=h,json=p).status_code==422
    assert client.post(f'/api/factories/{f}/scenarios/preview',headers=h,json={}).status_code==400

def test_round_trip(factory):
    h,f=factory;p=activity();p['processes']=[dict(name='Packaging <QA>',equipment='"Machine"',notes='Keep <this> & that', operating_hours=123,annual_energy_kwh=2000,primary_energy_source='Grid Electricity',operating_pressure_bar=5,estimated_leakage_percent=8)]
    p['energy_sources'].append(dict(source_type='Solar Electricity',annual_consumption=100,emission_factor=0,factor_source='Own factor'))
    assert client.post(f'/api/factories/{f}/data',headers=h,json=p).status_code==200
    saved=client.get(f'/api/factories/{f}/data',headers=h).json()
    for category,rows in p.items():
        assert len(saved[category])==len(rows)
        for actual,expected in zip(saved[category],rows):
            for key,value in expected.items():assert actual[key]==value

def test_double_baseline(factory):
    h,f=factory
    def submit(_):return client.post(f'/api/factories/{f}/data',headers=h,json=activity())
    with ThreadPoolExecutor(2) as pool:results=list(pool.map(submit,range(2)))
    assert all(r.status_code==200 for r in results),[r.text for r in results]
    assert len(client.get(f'/api/factories/{f}/data',headers=h).json()['energy_sources'])==1
    assert client.get(f'/api/factories/{f}/emissions/summary',headers=h).json()['baseline']==656.78

def test_factory_idempotency(owner):
    h,_=owner;h={**h,'Idempotency-Key':uuid.uuid4().hex}
    p=dict(name='Once',industry='Food',location='Nashik',reporting_period='2026',annual_production=1,production_unit='kg/year')
    with ThreadPoolExecutor(2) as pool:results=list(pool.map(lambda _:client.post('/api/factories',headers=h,json=p),range(2)))
    assert all(r.status_code==201 for r in results)
    assert results[0].json()['id']==results[1].json()['id']

def test_scenario_and_roadmap(factory):
    h,f=populated(factory)
    recs=client.get(f'/api/factories/{f}/recommendations',headers=h).json();rec=next(r for r in recs if r['carbon_saving_tco2e']>0)
    p=dict(recommendation_id=rec['id'],implementation_percent=50,performance_percent=80,cost_variation_percent=20)
    preview=client.post(f'/api/factories/{f}/scenarios/preview',headers=h,json=p);assert preview.status_code==200,preview.text
    hh={**h,'Idempotency-Key':uuid.uuid4().hex}
    with ThreadPoolExecutor(2) as pool:results=list(pool.map(lambda _:client.post(f'/api/factories/{f}/scenarios',headers=hh,json=p),range(2)))
    assert all(r.status_code==201 for r in results),[r.text for r in results]
    assert results[0].json()['id']==results[1].json()['id']
    for key,value in preview.json().items():assert results[0].json()[key]==value
    sid=results[0].json()['id']
    for _ in range(3):
        result=client.post(f'/api/factories/{f}/roadmap',headers=h,json={'preferred_scenario_id':sid});assert result.status_code==200,result.text
        assert result.json()['baseline_tco2e']==pytest.approx(656.8,abs=.1)
    assert len(client.get(f'/api/factories/{f}/scenarios',headers=h).json())==1

@pytest.mark.parametrize('endpoint',['','/data','/emissions/summary','/hotspots','/root-cause','/recommendations','/scenarios','/roadmap'])
def test_ownership(factory,endpoint):
    _,f=factory
    other=client.post('/api/auth/register',json=dict(name='Other',organization='Other',email=f'{uuid.uuid4().hex}@example.com',password='Password123')).json()
    h={'Authorization':'Bearer '+other['access_token']}
    assert client.get(f'/api/factories/{f}{endpoint}',headers=h).status_code==403
