"""Sargassum Watch API — auth, live weather, persisted reports, Grok explain."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.auth import create_token, get_current_user, hash_password, require_operations, verify_password
from app.db import get_conn, init_db, row_to_dict
from app.lib.explain import answer_question, explain_with_model, grok_status, ollama_status
from app.lib.fallback_explain import fallback_explanation
from app.models import AskIn, DemoPlayIn, ExplainIn, InspectionIn, LoginIn, RegisterIn, ReportIn, SettingsIn, ZoneEconomicsIn
from app.store import (
    create_municipality,
    ensure_demo_accounts,
    get_municipality,
    inspect_zone,
    play_demo,
    reset_desk,
    seed_shift,
    shift_briefing_text,
    snapshot,
    submit_report,
    update_settings,
    update_zone_economics,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    ensure_demo_accounts()
    yield


app = FastAPI(
    title="Sargassum Watch",
    description="Citizen reports → two lists (cleanup + scout). Grok explains the numbers. It never ranks.",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    grok = await grok_status()
    ollama = await ollama_status()
    return {
        "ok": True,
        "engine": "sargassum-watch",
        "storage": "sqlite",
        "weather": "open-meteo",
        "ai": grok,
        "grok": grok,
        "ollama": ollama,
    }


@app.post("/api/auth/register")
async def register(body: RegisterIn):
    conn = get_conn()
    if conn.execute("SELECT id FROM users WHERE email = ?", (body.email,)).fetchone():
        raise HTTPException(status_code=409, detail="An account with that email already exists")
    muni = create_municipality(body.municipality, body.region, body.lat, body.lng)
    cur = conn.execute(
        """
        INSERT INTO users (email, name, password_hash, role, municipality_id, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        """,
        (body.email, body.name, hash_password(body.password), body.role, muni["id"]),
    )
    conn.commit()
    user = row_to_dict(conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone())
    token = create_token(user)
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "municipality": muni["name"],
        },
    }


@app.post("/api/auth/login")
async def login(body: LoginIn):
    row = get_conn().execute("SELECT * FROM users WHERE email = ?", (body.email,)).fetchone()
    user = row_to_dict(row)
    if user is None or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    muni = get_municipality(int(user["municipality_id"]))
    token = create_token(user)
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "municipality": (muni or {}).get("name"),
        },
    }


@app.get("/api/me")
async def me(user: dict = Depends(get_current_user)):
    muni = get_municipality(int(user["municipality_id"]))
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "municipality": (muni or {}).get("name"),
    }


def _muni_for(user: dict) -> dict:
    muni = get_municipality(int(user["municipality_id"]))
    if muni is None:
        raise HTTPException(status_code=404, detail="Municipality not found")
    return muni


@app.get("/api/state")
async def get_state(user: dict = Depends(get_current_user)):
    return await snapshot(_muni_for(user), user=user)


@app.post("/api/reports")
async def post_report(body: ReportIn, user: dict = Depends(get_current_user)):
    try:
        return await submit_report(_muni_for(user), body.model_dump(), user)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/inspect")
async def post_inspect(body: InspectionIn, user: dict = Depends(require_operations)):
    try:
        return await inspect_zone(_muni_for(user), body.model_dump(), user)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.patch("/api/settings")
async def patch_settings(body: SettingsIn, user: dict = Depends(require_operations)):
    return await update_settings(_muni_for(user), body.model_dump(exclude_none=True), user)


@app.patch("/api/zones")
async def patch_zone(body: ZoneEconomicsIn, user: dict = Depends(require_operations)):
    try:
        return await update_zone_economics(
            _muni_for(user),
            body.zoneId,
            body.model_dump(exclude_none=True),
            user,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/demo/seed")
async def post_demo_seed(user: dict = Depends(require_operations)):
    return await seed_shift(_muni_for(user), user)


@app.post("/api/demo/reset")
async def post_demo_reset(user: dict = Depends(require_operations)):
    return await reset_desk(_muni_for(user), user)


@app.post("/api/demo/play")
async def post_demo_play(body: DemoPlayIn, user: dict = Depends(require_operations)):
    try:
        return await play_demo(_muni_for(user), body.eventId, user)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown demo event: {exc}") from exc


@app.get("/api/briefing")
async def get_briefing(user: dict = Depends(get_current_user)):
    state = await snapshot(_muni_for(user), user=user)
    return PlainTextResponse(shift_briefing_text(state))


@app.post("/api/explain")
async def post_explain(body: ExplainIn | None = None, user: dict = Depends(get_current_user)):
    state = body.summaryContext if body and body.summaryContext else await snapshot(_muni_for(user), user=user)
    return await explain_with_model(state)


@app.post("/api/ask")
async def post_ask(body: AskIn, user: dict = Depends(get_current_user)):
    state = body.summaryContext or await snapshot(_muni_for(user), user=user)
    return await answer_question(state, body.question)


@app.get("/api/explain/fallback")
async def get_fallback(user: dict = Depends(get_current_user)):
    return fallback_explanation(await snapshot(_muni_for(user), user=user))


DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        file = DIST / full_path
        if full_path and file.exists() and file.is_file():
            return FileResponse(file)
        return FileResponse(DIST / "index.html")
