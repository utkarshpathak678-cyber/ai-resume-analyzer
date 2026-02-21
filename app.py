from flask import Flask, render_template, request
import os
from PyPDF2 import PdfReader

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

JOB_SKILLS = {
    "Data Scientist": {
        "python": 3,
        "machine learning": 4,
        "pandas": 2,
        "numpy": 2,
        "sql": 3,
        "data analysis": 3
    },
    "Backend Developer": {
        "python": 3,
        "flask": 3,
        "django": 3,
        "sql": 3,
        "api": 2,
        "database": 2
    },
    "Frontend Developer": {
        "html": 3,
        "css": 3,
        "javascript": 4,
        "react": 4,
        "bootstrap": 2
    }
}

def extract_text_from_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text()
    return text.lower()

import re

def analyze_resume(text, job_role):
    required_skills = JOB_SKILLS[job_role]

    skill_scores = {}
    total_weighted_score = 0
    max_possible_score = 0

    for skill, weight in required_skills.items():
        count = len(re.findall(r"\b" + re.escape(skill) + r"\b", text))

        # proficiency based on frequency
        proficiency = min(count * 10, 100)

        weighted_score = proficiency * weight
        skill_scores[skill] = proficiency

        total_weighted_score += weighted_score
        max_possible_score += 100 * weight

    # Experience bonus
    experience_bonus = 0
    if "experience" in text:
        experience_bonus = 10

    # Project bonus
    project_bonus = 0
    if "project" in text:
        project_bonus = 5

    # Certification bonus
    certification_bonus = 0
    if "certification" in text or "certified" in text:
        certification_bonus = 5

    ats_score = int((total_weighted_score / max_possible_score) * 100)
    ats_score = min(ats_score + experience_bonus + project_bonus + certification_bonus, 100)

    found_skills = [skill for skill, score in skill_scores.items() if score > 0]
    missing_skills = [skill for skill, score in skill_scores.items() if score == 0]

    if ats_score >= 75:
        level = "ATS Approved 💼"
    elif ats_score >= 50:
        level = "Moderate Match ⚡"
    else:
        level = "Low Match 🔥"

    return found_skills, missing_skills, ats_score, level, skill_scores
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        file = request.files["resume"]
        job_role = request.form["job_role"]
        job_description = request.form.get("job_description", "").lower()

        if file:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)

            text = extract_text_from_pdf(filepath)

            found, missing, percentage, level, skill_strength = analyze_resume(text, job_role)

            # Highlight matched skills
            highlighted_text = text
            for skill in found:
                highlighted_text = re.sub(
                    r"\b" + re.escape(skill) + r"\b",
                    f"<mark style='background-color:yellow;color:black'>{skill}</mark>",
                    highlighted_text,
                    flags=re.IGNORECASE
                )

            # JD Matching Logic
            jd_keywords = re.findall(r"\b[a-zA-Z]+\b", job_description)
            jd_keywords = list(set(jd_keywords))

            resume_words = set(re.findall(r"\b[a-zA-Z]+\b", text))

            matched_jd_keywords = [word for word in jd_keywords if word in resume_words]
            missing_jd_keywords = [word for word in jd_keywords if word not in resume_words]

            jd_match_percentage = 0
            if jd_keywords:
                jd_match_percentage = int((len(matched_jd_keywords) / len(jd_keywords)) * 100)

            return render_template(
                "result.html",
                found=found,
                missing=missing,
                percentage=percentage,
                level=level,
                role=job_role,
                skill_strength=skill_strength,
                highlighted_text=highlighted_text[:2000],
                jd_match_percentage=jd_match_percentage,
                matched_jd_keywords=matched_jd_keywords[:20],
                missing_jd_keywords=missing_jd_keywords[:20]
            )

    return render_template("index.html", roles=JOB_SKILLS.keys())
if __name__ == "__main__":
    app.run(debug=True)