import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

import engine  # noqa: E402  (loads the AI model)

FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "pathwise")

app = FastAPI(
    title="Pathwise - AI Career Platform API",
    description="AI career prediction & skill gap analysis",
    version="2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    skills: list[str] = []


class GapRequest(BaseModel):
    career: str
    skills: list[str] = []


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/meta")
def get_meta():
    """Careers and skills the website shows."""
    return engine.meta()


@app.post("/api/career/predict")
def predict_career(data: PredictRequest):
    if not engine.clean_skills(data.skills):
        raise HTTPException(status_code=400, detail="Please select at least one skill.")
    return engine.predict(data.skills)


@app.post("/api/skill-gap")
def get_skill_gap(data: GapRequest):
    try:
        return engine.skill_gap(data.career, data.skills)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


# Serve the website itself (must be last, so the /api routes win)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="website")
