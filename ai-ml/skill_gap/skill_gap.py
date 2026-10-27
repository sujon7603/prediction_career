# ============================
# Career / skill knowledge base
# ============================

# Skills each career needs (keys match the ML model feature names)
CAREER_SKILLS = {
    "Data Scientist": {
        "python", "sql", "statistics",
        "machine_learning", "data_visualization", "data_analysis",
    },
    "Data Analyst": {
        "python", "sql", "statistics",
        "data_visualization", "data_analysis",
    },
    "Machine Learning Engineer": {
        "python", "machine_learning", "deep_learning", "statistics",
    },
    "Software Engineer": {
        "java", "python", "javascript", "html_css", "projects",
    },
    "Web Developer": {
        "javascript", "html_css", "web_development", "projects",
    },
    "Cybersecurity Analyst": {
        "cybersecurity", "communication", "projects",
    },
}

CAREER_INFO = {
    "Data Scientist": "Turns messy data into insights, forecasts and experiments.",
    "Data Analyst": "Interprets data and turns it into reports that guide business decisions.",
    "Machine Learning Engineer": "Builds and ships machine learning models that run reliably in production.",
    "Software Engineer": "Designs, builds and maintains software applications.",
    "Web Developer": "Builds and maintains websites and web applications.",
    "Cybersecurity Analyst": "Protects systems and data from security threats.",
}

# label shown on the website + estimated weeks to learn (about 6 hours a week)
SKILL_INFO = {
    "python":             ("Python", 4),
    "sql":                ("SQL", 3),
    "statistics":         ("Statistics", 5),
    "data_analysis":      ("Data Analysis", 3),
    "data_visualization": ("Data Visualization", 3),
    "machine_learning":   ("Machine Learning", 6),
    "deep_learning":      ("Deep Learning", 8),
    "html_css":           ("HTML & CSS", 3),
    "javascript":         ("JavaScript", 5),
    "java":               ("Java", 6),
    "web_development":    ("Web Development", 5),
    "cybersecurity":      ("Cybersecurity", 8),
    "communication":      ("Communication", 2),
    "projects":           ("Personal Projects", 4),
}

# Sensible learning order (foundations first)
LEARN_ORDER = [
    "python", "sql", "html_css", "statistics", "data_analysis",
    "data_visualization", "javascript", "java", "web_development",
    "machine_learning", "deep_learning", "cybersecurity",
    "communication", "projects",
]


def skill_label(key):
    return SKILL_INFO.get(key, (key.replace("_", " ").title(), 4))[0]


def skill_weeks(key):
    return SKILL_INFO.get(key, (key, 4))[1]


def _order(key):
    return LEARN_ORDER.index(key) if key in LEARN_ORDER else 99


# ============================
# Skill Gap Calculation
# ============================

def calculate_skill_gap(student_skills, career):
    required = CAREER_SKILLS.get(career, set())
    student_skills = set(student_skills)

    matching = required.intersection(student_skills)
    missing = required - student_skills

    match_score = (len(matching) / len(required) * 100) if required else 0

    return {
        "career": career,
        "matching_skills": sorted(matching, key=_order),
        "missing_skills": sorted(missing, key=_order),
        "match_score": round(match_score, 2),
    }


if __name__ == "__main__":
    result = calculate_skill_gap(
        ["python", "sql", "statistics", "machine_learning"], "Data Scientist"
    )
    print("Career  :", result["career"])
    print("Have    :", result["matching_skills"])
    print("Missing :", result["missing_skills"])
    print("Match   :", str(result["match_score"]) + "%")
