import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from app.database import engine, Base
from app.routers import auth, factories, data_entry, emissions, hotspots, root_cause, recommendations, simulator, roadmap

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Carbon Core API",
    description="Deterministic industrial carbon accounting, hotspot detection, and decarbonization engine.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth.router)
app.include_router(factories.router)
app.include_router(data_entry.router)
app.include_router(emissions.router)
app.include_router(hotspots.router)
app.include_router(root_cause.router)
app.include_router(recommendations.router)
app.include_router(simulator.router)
app.include_router(roadmap.router)

BASE_DIR = Path(__file__).resolve().parent.parent

def find_file(filename: str) -> Path:
    candidates = [
        BASE_DIR / "frontend" / "dist" / filename,
        BASE_DIR / "frontend" / filename,
        BASE_DIR / filename
    ]
    for c in candidates:
        if c.exists():
            return c
    # Fallback checks
    if filename == "factory-setup.html":
        reg = BASE_DIR / "register.html"
        if reg.exists():
            return reg
        reg_fe = BASE_DIR / "frontend" / "register.html"
        if reg_fe.exists():
            return reg_fe
    return candidates[-1]

@app.get("/")
def serve_root():
    p = find_file("index.html")
    if p.exists():
        return FileResponse(p, media_type="text/html")
    raise HTTPException(status_code=404, detail="index.html not found")

@app.get("/index.html")
def serve_index():
    p = find_file("index.html")
    if p.exists():
        return FileResponse(p, media_type="text/html")
    raise HTTPException(status_code=404, detail="index.html not found")

@app.get("/login.html")
def serve_login():
    p = find_file("login.html")
    if p.exists():
        return FileResponse(p, media_type="text/html")
    raise HTTPException(status_code=404, detail="login.html not found")

@app.get("/register.html")
def serve_register_redirect():
    # If factory-setup exists, serve it or redirect
    p = find_file("factory-setup.html")
    if p.exists():
        return FileResponse(p, media_type="text/html")
    return RedirectResponse(url="/factory-setup.html")

@app.get("/factory-setup.html")
def serve_factory_setup():
    p = find_file("factory-setup.html")
    if p.exists():
        return FileResponse(p, media_type="text/html")
    raise HTTPException(status_code=404, detail="factory-setup.html not found")

@app.get("/factory-data.html")
def serve_factory_data():
    p = find_file("factory-data.html")
    if p.exists():
        return FileResponse(p, media_type="text/html")
    raise HTTPException(status_code=404, detail="factory-data.html not found")

@app.get("/dashboard.html")
def serve_dashboard():
    p = find_file("dashboard.html")
    if p.exists():
        return FileResponse(p, media_type="text/html")
    raise HTTPException(status_code=404, detail="dashboard.html not found")

@app.get("/leak-detector.html")
def serve_leak_detector():
    p = find_file("leak-detector.html")
    if p.exists():
        return FileResponse(p, media_type="text/html")
    raise HTTPException(status_code=404, detail="leak-detector.html not found")

@app.get("/root-cause.html")
def serve_root_cause():
    p = find_file("root-cause.html")
    if p.exists():
        return FileResponse(p, media_type="text/html")
    raise HTTPException(status_code=404, detail="root-cause.html not found")

@app.get("/solutions.html")
def serve_solutions():
    p = find_file("solutions.html")
    if p.exists():
        return FileResponse(p, media_type="text/html")
    raise HTTPException(status_code=404, detail="solutions.html not found")

@app.get("/simulator.html")
def serve_simulator():
    p = find_file("simulator.html")
    if p.exists():
        return FileResponse(p, media_type="text/html")
    raise HTTPException(status_code=404, detail="simulator.html not found")

@app.get("/roadmap.html")
def serve_roadmap():
    p = find_file("roadmap.html")
    if p.exists():
        return FileResponse(p, media_type="text/html")
    raise HTTPException(status_code=404, detail="roadmap.html not found")

@app.get("/api.js")
def serve_api_js():
    p = find_file("api.js")
    if not p.exists():
        p = BASE_DIR / "frontend" / "src" / "js" / "api.js"
    if p.exists():
        return FileResponse(p, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="api.js not found")

# Static mounting
frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
else:
    app.mount("/", StaticFiles(directory=str(BASE_DIR), html=True), name="static")
