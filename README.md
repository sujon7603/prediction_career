# Pathwise - AI Career Prediction & Skill Gap Analysis

One website, one command. The Python backend (FastAPI + scikit-learn) also serves the website.

## Run it
**Windows:** double-click `run.bat`, wait for the browser to open (first run installs packages, needs internet).
**Mac / Linux:** `bash run.sh`

Then open http://localhost:8000 (opens automatically).
Requires Python 3.9+ installed. To stop: close the window.

## How to use the website
1. Tap the skills you have, press **Predict my career** -> ranked careers with AI confidence and skill match.
2. Pick any other career in **Skill gap for any career** -> missing skills + learning plan with weeks.

## Folders
- `pathwise/`   website (index.html, script.js, style.css)
- `ai-ml/`      backend
  - `api/app.py`            web server + API endpoints
  - `engine.py`             loads the model, predicts, computes skill gap
  - `skill_gap/skill_gap.py`  careers, required skills, learning weeks (edit here to add careers/skills)
  - `data/career_dataset.csv` training data, `models/career_model.pkl` trained model

API docs: http://localhost:8000/docs

## Retrain the model (optional)
Edit `ai-ml/data/career_dataset.csv`, then in `ai-ml`: `python -m training.train_model`
If the saved model cannot load on your computer, the app trains a new one automatically.
