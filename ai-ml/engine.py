"""All AI logic (no web code here): model loading, prediction, skill gap."""
import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier

from skill_gap.skill_gap import (
    CAREER_SKILLS, CAREER_INFO, LEARN_ORDER,
    calculate_skill_gap, skill_label, skill_weeks,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "career_model.pkl")
DATA_PATH = os.path.join(BASE_DIR, "data", "career_dataset.csv")

# Same column order the model was trained with
FEATURES = [
    "python", "sql", "statistics", "machine_learning", "deep_learning",
    "data_visualization", "java", "javascript", "html_css", "cybersecurity",
    "communication", "data_analysis", "web_development", "projects",
]


def _blank_row():
    return pd.DataFrame([[0] * len(FEATURES)], columns=FEATURES)


def load_model():
    """Load the saved model. If it cannot be used (for example it was saved
    with a different scikit-learn version), train a fresh one from the CSV."""
    try:
        model = joblib.load(MODEL_PATH)
        model.predict_proba(_blank_row())  # make sure it really works
        return model
    except Exception as err:
        print("[engine] Could not use saved model (%s). Training a new one..." % err)
        df = pd.read_csv(DATA_PATH)
        model = RandomForestClassifier(n_estimators=200, random_state=42)
        model.fit(df[FEATURES], df["career"])
        try:
            joblib.dump(model, MODEL_PATH)
        except Exception:
            pass
        return model


model = load_model()


def normalize_skill(skill):
    s = str(skill).strip().lower()
    for ch in (" ", "/", "-", "&"):
        s = s.replace(ch, "_")
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")


def clean_skills(skills):
    return {s for s in (normalize_skill(x) for x in skills) if s in FEATURES}


def _order(key):
    return LEARN_ORDER.index(key) if key in LEARN_ORDER else 99


def meta():
    careers = []
    for name, req in CAREER_SKILLS.items():
        careers.append({
            "name": name,
            "description": CAREER_INFO.get(name, ""),
            "skills": [{"key": k, "label": skill_label(k)} for k in sorted(req, key=_order)],
        })
    skills = [{"key": k, "label": skill_label(k)} for k in LEARN_ORDER if k in FEATURES]
    return {"skills": skills, "careers": careers}


def predict(skills):
    skill_set = clean_skills(skills)
    row = pd.DataFrame([{f: (1 if f in skill_set else 0) for f in FEATURES}], columns=FEATURES)

    probabilities = model.predict_proba(row)[0]
    ai_conf = {c: float(p) for c, p in zip(model.classes_, probabilities)}

    results = []
    for career in CAREER_SKILLS:
        gap = calculate_skill_gap(skill_set, career)
        results.append({
            "career": career,
            "description": CAREER_INFO.get(career, ""),
            "ai_confidence": round(ai_conf.get(career, 0.0) * 100, 1),
            "skill_match": gap["match_score"],
            "matching_skills": [skill_label(k) for k in gap["matching_skills"]],
            "missing_skills": [skill_label(k) for k in gap["missing_skills"]],
        })

    # Best fit = highest AI confidence, ties broken by skill match
    results.sort(key=lambda r: (r["ai_confidence"], r["skill_match"]), reverse=True)
    return {"predicted_career": results[0]["career"], "careers": results}


def skill_gap(career, skills):
    if career not in CAREER_SKILLS:
        raise ValueError("Unknown career: %s" % career)
    skill_set = clean_skills(skills)
    gap = calculate_skill_gap(skill_set, career)

    missing = [
        {"key": k, "label": skill_label(k), "weeks": skill_weeks(k)}
        for k in gap["missing_skills"]
    ]
    return {
        "career": career,
        "description": CAREER_INFO.get(career, ""),
        "match_score": gap["match_score"],
        "matching": [{"key": k, "label": skill_label(k)} for k in gap["matching_skills"]],
        "missing": missing,
        "total_weeks": sum(m["weeks"] for m in missing),
    }
