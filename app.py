import csv
import io
import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, Response, abort, flash, redirect, render_template, request, session, url_for

APP_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("FEEDBACK_DB", APP_DIR / "feedback.db"))
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-this-password")
RATING_FIELDS = {
    "clarity": "Concept clarity",
    "knowledge": "Subject knowledge",
    "organisation": "Lecture organisation",
    "examples": "Real-world examples",
    "interaction": "Questions and discussion",
    "doubts": "Doubt solving",
    "materials": "Study materials",
    "pace": "Teaching pace",
    "labs": "Lab demonstrations",
    "practical": "Practical relevance",
    "handsOn": "Hands-on opportunities",
    "security": "IoT safety and security",
}
TOPIC_OPTIONS = [
    "Sensors and actuators", "Arduino or ESP32", "Raspberry Pi", "IoT protocols",
    "Cloud and dashboards", "IoT security", "Smart home or city projects", "Data analysis"
]

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect_db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            student_name TEXT NOT NULL,
            student_id TEXT,
            department TEXT NOT NULL,
            year TEXT NOT NULL,
            teacher TEXT NOT NULL,
            semester TEXT NOT NULL,
            ratings_json TEXT NOT NULL,
            topics_json TEXT NOT NULL,
            overall INTEGER NOT NULL,
            best_part TEXT,
            improve TEXT NOT NULL,
            suggestion TEXT,
            recommend TEXT
        )""")

init_db()

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/submit")
def submit():
    required = ["studentName", "department", "year", "teacher", "semester", "improve"]
    values = {key: request.form.get(key, "").strip() for key in required}
    if any(not value for value in values.values()):
        flash("Please complete all required fields and try again.", "error")
        return redirect(url_for("index") + "#feedbackForm")

    ratings = {}
    for key, label in RATING_FIELDS.items():
        raw = request.form.get(key, "")
        if raw:
            try:
                score = int(raw)
            except ValueError:
                abort(400, "Invalid rating.")
            if score not in range(1, 6):
                abort(400, "Ratings must be between 1 and 5.")
            ratings[label] = score

    overall_raw = request.form.get("overall", "")
    try:
        overall = int(overall_raw)
    except ValueError:
        abort(400, "Please select an overall rating.")
    if overall not in range(1, 6):
        abort(400, "Overall rating must be between 1 and 5.")

    topics = [topic for topic in request.form.getlist("topics") if topic in TOPIC_OPTIONS]
    student_id = request.form.get("studentId", "").strip()[:80]
    best_part = request.form.get("bestPart", "").strip()[:3000]
    improve = values["improve"][:3000]
    suggestion = request.form.get("suggestion", "").strip()[:3000]
    recommend = request.form.get("recommend", "").strip()[:80]
    with connect_db() as conn:
        conn.execute("""
        INSERT INTO feedback (created_at, student_name, student_id, department, year,
          teacher, semester, ratings_json, topics_json, overall, best_part, improve, suggestion, recommend)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            values["studentName"][:120], student_id, values["department"][:120],
            values["year"][:80], values["teacher"][:120], values["semester"][:40],
            json.dumps(ratings), json.dumps(topics), overall, best_part, improve, suggestion, recommend
        ))
    flash("Thank you! Your feedback was submitted and saved successfully.", "success")
    return redirect(url_for("index") + "#feedbackForm")

@app.get("/admin/login")
def admin_login():
    return render_template_string_login()

def render_template_string_login(error=""):
    from flask import render_template_string
    return render_template_string("""<!doctype html><html lang="en"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin Login</title>
    <style>body{font-family:system-ui;background:#f4f7fc;display:grid;place-items:center;min-height:100vh;color:#17233f}.box{background:white;padding:30px;border-radius:16px;width:min(360px,85vw);box-shadow:0 10px 40px #0001}input{width:100%;padding:12px;box-sizing:border-box;margin:8px 0 15px;border:1px solid #ccd5e5;border-radius:8px}button{background:#3157d5;color:white;border:0;padding:12px;border-radius:8px;width:100%;font-weight:700}p{color:#b22}small{color:#66738e}</style>
    <div class="box"><h2>Feedback Admin</h2><small>Sign in to view submitted responses.</small>{% if error %}<p>{{ error }}</p>{% endif %}<form method="post"><label>Admin password</label><input name="password" type="password" required autofocus><button>Sign in</button></form></div></html>""", error=error)

@app.post("/admin/login")
def admin_login_post():
    if secrets.compare_digest(request.form.get("password", ""), ADMIN_PASSWORD):
        session["admin_logged_in"] = True
        return redirect(request.args.get("next") or url_for("admin"))
    return render_template_string_login("Incorrect password."), 401

@app.post("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

@app.get("/admin")
@admin_required
def admin():
    with connect_db() as conn:
        rows = conn.execute("SELECT * FROM feedback ORDER BY id DESC").fetchall()
    responses = []
    for row in rows:
        item = dict(row)
        item["ratings"] = json.loads(item.pop("ratings_json"))
        item["topics"] = json.loads(item.pop("topics_json"))
        responses.append(item)
    return render_template("admin.html", responses=responses, total=len(responses))

@app.get("/admin/export.csv")
@admin_required
def export_csv():
    with connect_db() as conn:
        rows = conn.execute("SELECT * FROM feedback ORDER BY id DESC").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Submitted at", "Student name", "Student ID", "Department", "Year",
                     "Teacher", "Semester", "Ratings JSON", "Topics", "Overall rating",
                     "Liked", "Improvements", "Other suggestions", "Recommend"])
    for row in rows:
        item = dict(row)
        writer.writerow([item["id"], item["created_at"], item["student_name"], item["student_id"],
                         item["department"], item["year"], item["teacher"], item["semester"],
                         item["ratings_json"], item["topics_json"], item["overall"],
                         item["best_part"], item["improve"], item["suggestion"], item["recommend"]])
    return Response("\ufeff" + output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=iot_feedback_responses.csv"})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)
