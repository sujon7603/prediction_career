import os
import pandas as pd
import joblib
import sys


# ============================
# Find The Project Directory
# ============================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# ============================
# Allow importing skill gap
# ============================

sys.path.append(BASE_DIR)

from skill_gap.skill_gap import calculate_skill_gap


# ============================
# Load Trained Model
# ============================

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "career_model.pkl"
)


model = joblib.load(MODEL_PATH)

print("Career Prediction Model Successfully!")


# ============================
# New Student Profile
# ============================

student_skills = [
    "python",
    "sql",
    "statistics",
    "machine_learning"
]

student = pd.DataFrame([{
    "python": 1,
    "sql": 1,
    "statistics":1,
    "machine_learning": 1,
    "deep_learning": 0,
    "data_visualization": 1,
    "java" : 0,
    "javascript": 0,
    "html_css": 0,
    "cybersecurity": 0,
    "communication": 1,
    "data_analysis": 1,
    "web_development": 0,
    "projects": 1
}])

# ============================
# Predict Career
# ============================

prediction = model.predict(student)

predicted_career = prediction[0]

# ============================
# Get Probabilities
# ============================

probabilities = model.predict_proba(student)

classes = model.classes_

results = sorted(
    zip(classes, probabilities[0]),
    key = lambda x: x[1],
    reverse=True      
)


# ============================
# Skill gap analysis
# ============================

skill_result = calculate_skill_gap(
    student_skills,
    predicted_career
)


# ============================
# Display Complete Result
# ============================

print("=========================")
print("   AI CAREER ANALYSIS")
print("=========================")

print("\nPredicted Career : ")
print(predicted_career)


print("\nCareer Prediction Probabilities : ")

for career, probability in results:
    print(
        f"{career}: {probability:.2%}" 
    )



print("\n=======================")

print("matching Skills : ")

for skill in skill_result["matching_skills"]:
    print("✅", skill)

print("\nMissing Skills : ")

for skill in skill_result["missing_skills"]:
    print("❎", skill)


print("\nSkill match score : ")
print(f'{skill_result["match_score"]}%')
                          
print("\n=======================")