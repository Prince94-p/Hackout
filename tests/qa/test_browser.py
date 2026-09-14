"""Browser reproduction against the same isolated-schema application."""
import socket
import threading
import time
import uuid
from pathlib import Path
import pytest
import uvicorn
from playwright.sync_api import sync_playwright
from app.main import app

@pytest.fixture(scope='module')
def browser_env():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='warning'))
    thread=threading.Thread(target=server.run,daemon=True);thread.start()
    for _ in range(100):
        if server.started:break
        time.sleep(.1)
    with sync_playwright() as p:
        executable=next(Path('/Applications').glob('Google Chrome*.app/Contents/MacOS/Google Chrome'))
        browser=p.chromium.launch(executable_path=str(executable),headless=True,args=['--no-sandbox'])
        yield browser,f'http://127.0.0.1:{port}'
        browser.close()
    server.should_exit=True;thread.join(timeout=10)

@pytest.fixture
def page(browser_env):
    browser,base=browser_env
    context=browser.new_context(base_url=base)
    page=context.new_page();page.set_default_navigation_timeout(15000);page.on('dialog',lambda d:d.accept())
    yield page
    context.close()

def register(page,name='QA Browser'):
    email=f'qa-browser-{uuid.uuid4().hex}@example.com'
    r=page.request.post('/api/auth/register',data=dict(name=name,organization='Browser Org',email=email,password='BrowserPassword123!'))
    assert r.status==201,r.text()
    return r.json(),email

def authenticate(page,user):
    page.goto('/index.html',wait_until='domcontentloaded')
    page.evaluate('(user)=>{localStorage.clear();sessionStorage.clear();localStorage.setItem("authToken",user.access_token);}',user)

def create_factory(page,user,data=True):
    h={'Authorization':'Bearer '+user['access_token']}
    r=page.request.post('/api/factories',headers=h,data=dict(name='Browser Factory',industry='Textiles',location='Surat',reporting_period='2026',annual_production=100,production_unit='units/year'))
    assert r.status==201,r.text()
    fid=r.json()['id'];page.evaluate('(id)=>localStorage.setItem("activeFactoryId",id)',fid)
    if data:
        payload=dict(energy_sources=[dict(source_type='Grid Electricity',annual_consumption=420000,emission_factor=.5,factor_source='QA Factor')],material_inputs=[dict(material_type='Fabric',annual_quantity=100000,emission_factor=5,recycled_content_percent=10)],processes=[dict(name='Compressed Air System',annual_energy_kwh=100000,estimated_leakage_percent=28,operating_pressure_bar=7.5)],waste_streams=[dict(waste_type='Offcuts',annual_quantity=8000,emission_factor=1.5,treatment_method='External Recycling')])
        r=page.request.post(f'/api/factories/{fid}/data',headers=h,data=payload);assert r.status==200,r.text()
    return fid

def settle(page):
    page.wait_for_function("!document.querySelector('.content') || getComputedStyle(document.querySelector('.content')).visibility === 'visible'",timeout=60000)

def test_mobile_landing(page):
    page.set_viewport_size({'width':390,'height':844});page.goto('/index.html',wait_until='domcontentloaded')
    assert page.evaluate('document.documentElement.scrollWidth')<=390, page.locator('body *').evaluate_all('(els)=>els.filter(e=>e.getBoundingClientRect().right>390).map(e=>[e.tagName,e.className,e.getBoundingClientRect().right]).slice(0,20)')
    box=page.locator('.nav-btn').bounding_box();assert box['x']+box['width']<=390

def test_invalid_login_recovery(page):
    user,email=register(page);page.goto('/login.html',wait_until='domcontentloaded')
    page.locator('#loginEmail').fill(email);page.locator('#loginPassword').fill('WrongPassword')
    page.locator('#privacyPolicyCheckLogin').check()
    page.locator('#loginForm').evaluate('(form)=>form.requestSubmit()')
    page.wait_for_function("document.querySelector('#loginMessage').textContent.includes('Invalid')")
    assert page.locator('#loginEmail').input_value()==email
    assert page.locator('#loginMessage').is_visible()
    page.locator('.forgot').click();assert 'Unavailable' in page.locator('.forgot').inner_text()

def test_pages_and_mobile(page):
    user,_=register(page);authenticate(page,user);fid=create_factory(page,user)
    errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
    unexpected=[];page.on('response',lambda r:unexpected.append(r.url) if r.status>=500 else None)
    for path in ['dashboard.html','factory-data.html','leak-detector.html?hotspot=waste','root-cause.html?hotspot=waste','solutions.html','simulator.html','roadmap.html']:
        page.goto('/'+path);settle(page)
        page.wait_for_function("document.querySelector('.profile strong')?.textContent === 'QA Browser'",timeout=60000)
        assert 'Surat' in page.locator('.factory-meta').inner_text()
        page.set_viewport_size({'width':390,'height':844})
        page.wait_for_timeout(350)
        assert page.evaluate('document.documentElement.scrollWidth')<=390,(path,page.locator('body *').evaluate_all('(els)=>els.filter(e=>e.getBoundingClientRect().right>391).map(e=>[e.tagName,e.className,e.getBoundingClientRect().right]).slice(0,15)'))
        page.set_viewport_size({'width':1280,'height':900})
    assert not errors,errors
    assert not unexpected,unexpected

def test_form_round_trip_and_add_buttons(page):
    user,_=register(page);authenticate(page,user);fid=create_factory(page,user,data=False)
    page.goto('/factory-data.html');settle(page)
    assert page.locator('.energy-amount-input').input_value()==''
    page.evaluate('addEnergyStream();addMaterialStream();addProcessStream();addWasteStream()')
    for cls in ['energy','material','process','waste']:assert page.locator(f'.{cls}-stream-row').count()==2
    page.locator('.energy-amount-input').first.fill('420000');page.locator('.energy-factor-input').first.fill('0.5')
    page.evaluate('goToPanel(1)')
    page.locator('.material-name-input').first.fill('Fabric "quoted" <safe>')
    page.locator('.material-amount-input').first.fill('100000');page.locator('.material-factor-input').first.fill('5')
    page.evaluate('goToPanel(3)')
    page.locator('.waste-type-input').first.fill('Offcuts');page.locator('.waste-amount-input').first.fill('8000');page.locator('.waste-factor-input').first.fill('1.5')
    page.evaluate('calculateBaseline();calculateBaseline()');page.wait_for_url('**/dashboard.html',timeout=60000)
    page.goto('/factory-data.html');settle(page)
    assert page.locator('.material-name-input').input_value()=='Fabric "quoted" <safe>'
    assert page.locator('.energy-stream-row').count()==1
    assert page.locator('button[title="Draft saving is unavailable"]').first.is_disabled()

def test_simulator_save_switch_and_empty(page):
    user,_=register(page,'Owner C');authenticate(page,user);create_factory(page,user)
    page.goto('/simulator.html');settle(page)
    assert page.locator('#baselineDisplay').inner_text()=='722'
    page.evaluate("document.querySelector('#implementationRange').value=50;document.querySelector('#performanceRange').value=80;document.querySelector('#costRange').value=20;updateScenario()")
    page.wait_for_timeout(1500)
    page.evaluate('addToRoadmap();addToRoadmap()');page.wait_for_url('**/roadmap.html',timeout=60000);settle(page)
    page.locator('.logout-btn').click();page.wait_for_url('**/login.html',timeout=60000)
    other,_=register(page,'Owner B');authenticate(page,other);create_factory(page,other,data=False)
    page.goto('/roadmap.html');settle(page)
    assert 'No roadmap available' in page.locator('.content').inner_text()
    assert not page.evaluate("localStorage.getItem('carbonScenario')")
    page.goto('/simulator.html');settle(page)
    assert 'No carbon calculation' in page.locator('.content').inner_text()
    assert page.locator('#baselineDisplay').count()==0
