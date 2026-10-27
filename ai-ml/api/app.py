import os
import sys

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

import auth    # noqa: E402  (login / signup logic)
import engine  # noqa: E402  (loads the AI model)

FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "pathwise")
COOKIE_NAME = "pathwise_session"

auth.init_db()

app = FastAPI(
    title="Pathwise - AI Career Platform API",
    description="AI career prediction & skill gap analysis (login required)",
    version="3.0",
)

# Pages anyone can open without logging in (everything else needs a login)
PUBLIC_PATHS = {"/login", "/signup", "/login.html", "/style.css", "/auth.js"}


# ============================
# Gate: no login -> no website
# ============================

@app.middleware("http")
async def require_login(request: Request, call_next):
    path = request.url.path
    is_public = (
        path.startswith("/api/")        # API endpoints check the login themselves
        or path.startswith("/img/")
        or path in PUBLIC_PATHS
    )
    if not is_public:
        user = auth.get_user_by_token(request.cookies.get(COOKIE_NAME))
        if not user:
            return RedirectResponse("/login", status_code=303)

    response = await call_next(request)
    if not path.startswith("/api/"):
        # Always load the newest files and never show a cached private page
        response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


def current_user(request: Request):
    user = auth.get_user_by_token(request.cookies.get(COOKIE_NAME))
    if not user:
        raise HTTPException(status_code=401, detail="Please log in.")
    return user


# ============================
# Request shapes
# ============================

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class PredictRequest(BaseModel):
    skills: list[str] = []


class GapRequest(BaseModel):
    career: str
    skills: list[str] = []


def _start_session(request: Request, response: Response, user):
    token = auth.create_session(user["id"])
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=auth.SESSION_SECONDS,
        httponly=True,                              # JavaScript cannot read it
        samesite="lax",                             # blocks cross-site requests
        secure=(request.url.scheme == "https"),     # https only when deployed
        path="/",
    )


# ============================
# Login / signup pages
# ============================

def _auth_page(request: Request):
    if auth.get_user_by_token(request.cookies.get(COOKIE_NAME)):
        return RedirectResponse("/", status_code=303)
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))


@app.get("/login", include_in_schema=False)
def login_page(request: Request):
    return _auth_page(request)


@app.get("/signup", include_in_schema=False)
def signup_page(request: Request):
    return _auth_page(request)


# ============================
# Auth API
# ============================

@app.post("/api/auth/signup")
def signup(data: SignupRequest, request: Request, response: Response):
    try:
        user = auth.create_user(data.name, data.email, data.password)
    except auth.AuthError as err:
        raise HTTPException(status_code=err.status, detail=err.message)
    _start_session(request, response, user)
    return {"user": user}


@app.post("/api/auth/login")
def login(data: LoginRequest, request: Request, response: Response):
    ip = request.client.host if request.client else "unknown"
    key = ip + "|" + data.email.strip().lower()
    try:
        auth.check_not_locked(key)
    except auth.AuthError as err:
        raise HTTPException(status_code=err.status, detail=err.message)

    user = auth.authenticate(data.email, data.password)
    if not user:
        auth.record_failure(key)
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    auth.clear_failures(key)
    _start_session(request, response, user)
    return {"user": user}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response):
    auth.delete_session(request.cookies.get(COOKIE_NAME))
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "logged out"}


@app.get("/api/auth/me")
def me(user=Depends(current_user)):
    return {"user": user}


# ============================
# AI API (login required)
# ============================

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/meta")
def get_meta(user=Depends(current_user)):
    """Careers and skills the website shows."""
    return engine.meta()


@app.post("/api/career/predict")
def predict_career(data: PredictRequest, user=Depends(current_user)):
    if not engine.clean_skills(data.skills):
        raise HTTPException(status_code=400, detail="Please select at least one skill.")
    return engine.predict(data.skills)


@app.post("/api/skill-gap")
def get_skill_gap(data: GapRequest, user=Depends(current_user)):
    try:
        return engine.skill_gap(data.career, data.skills)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


# ============================
# The website files (last, so the routes above win)
# ============================

print("[Pathwise] Serving website files from:", FRONTEND_DIR)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="website")
