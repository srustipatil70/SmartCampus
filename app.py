from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "smartcampus-secret-key"


# =========================
# DATABASE INITIALIZATION
# =========================

def init_db():
    conn = sqlite3.connect("smartcampus.db")
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Study plans table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    # Assignments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            title TEXT NOT NULL,
            due_date TEXT NOT NULL
        )
    """)

    # Attendance table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT UNIQUE NOT NULL,
            attended INTEGER NOT NULL,
            total INTEGER NOT NULL
        )
    """)

    # Notices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return render_template("home.html")


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("smartcampus.db")
        cursor = conn.cursor()

        try:

            cursor.execute("""
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
            """, (name, email, password))

            conn.commit()
            conn.close()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            conn.close()

            return "Email already registered."

    return render_template("register.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("smartcampus.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, email
            FROM users
            WHERE email = ? AND password = ?
        """, (email, password))

        user = cursor.fetchone()

        conn.close()

        if user:

            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["user_email"] = user[2]

            return redirect(url_for("dashboard"))

        return "Invalid email or password."

    return render_template("login.html")


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect("smartcampus.db")
    cursor = conn.cursor()

    # Study plan count
    cursor.execute("""
        SELECT COUNT(*)
        FROM study_plans
    """)

    study_count = cursor.fetchone()[0]

    # Assignment count
    cursor.execute("""
        SELECT COUNT(*)
        FROM assignments
    """)

    assignment_count = cursor.fetchone()[0]

    # Attendance
    cursor.execute("""
        SELECT attended, total
        FROM attendance
    """)

    attendance_records = cursor.fetchall()

    if attendance_records:

        total_attended = sum(
            row[0] for row in attendance_records
        )

        total_classes = sum(
            row[1] for row in attendance_records
        )

        if total_classes > 0:

            attendance_percentage = round(
                (total_attended / total_classes) * 100,
                1
            )

        else:

            attendance_percentage = 0

    else:

        attendance_percentage = 0

    # Notice count
    cursor.execute("""
        SELECT COUNT(*)
        FROM notices
    """)

    notice_count = cursor.fetchone()[0]

    # Next assignment
    cursor.execute("""
        SELECT subject, title, due_date
        FROM assignments
        ORDER BY due_date
        LIMIT 1
    """)

    upcoming_assignment = cursor.fetchone()

    conn.close()

    user_name = session.get(
        "user_name",
        "Student"
    )

    return render_template(
        "dashboard.html",
        user_name=user_name,
        study_count=study_count,
        assignment_count=assignment_count,
        attendance_percentage=attendance_percentage,
        notice_count=notice_count,
        upcoming_assignment=upcoming_assignment
    )


# =========================
# TIMETABLE
# =========================

@app.route("/timetable")
def timetable():

    return render_template(
        "timetable.html"
    )


# =========================
# STUDY PLANNER
# =========================

@app.route(
    "/study-planner",
    methods=["GET", "POST"]
)
def study_planner():

    conn = sqlite3.connect("smartcampus.db")
    cursor = conn.cursor()

    if request.method == "POST":

        subject = request.form["subject"]
        topic = request.form["topic"]
        date = request.form["date"]

        cursor.execute("""
            INSERT INTO study_plans
            (subject, topic, date)
            VALUES (?, ?, ?)
        """, (
            subject,
            topic,
            date
        ))

        conn.commit()

    cursor.execute("""
        SELECT *
        FROM study_plans
        ORDER BY date
    """)

    plans = cursor.fetchall()

    conn.close()

    return render_template(
        "study_planner.html",
        plans=plans
    )


# =========================
# ASSIGNMENTS
# =========================

@app.route(
    "/assignments",
    methods=["GET", "POST"]
)
def assignments():

    conn = sqlite3.connect("smartcampus.db")
    cursor = conn.cursor()

    if request.method == "POST":

        subject = request.form["subject"]
        title = request.form["title"]
        due_date = request.form["due_date"]

        cursor.execute("""
            INSERT INTO assignments
            (subject, title, due_date)
            VALUES (?, ?, ?)
        """, (
            subject,
            title,
            due_date
        ))

        conn.commit()

    cursor.execute("""
        SELECT *
        FROM assignments
        ORDER BY due_date
    """)

    assignments_data = cursor.fetchall()

    conn.close()

    return render_template(
        "assignments.html",
        assignments=assignments_data
    )


# =========================
# ATTENDANCE
# =========================

@app.route(
    "/attendance",
    methods=["GET", "POST"]
)
def attendance():

    conn = sqlite3.connect("smartcampus.db")
    cursor = conn.cursor()

    if request.method == "POST":

        subject = request.form["subject"]
        attended = int(
            request.form["attended"]
        )
        total = int(
            request.form["total"]
        )

        if total <= 0:

            conn.close()

            return "Total classes must be greater than 0."

        if attended > total:

            conn.close()

            return "Classes attended cannot be greater than total classes."

        cursor.execute("""
            INSERT OR REPLACE INTO attendance
            (subject, attended, total)
            VALUES (?, ?, ?)
        """, (
            subject,
            attended,
            total
        ))

        conn.commit()

    cursor.execute("""
        SELECT
            subject,
            attended,
            total,
            ROUND(
                (CAST(attended AS FLOAT) / total) * 100,
                2
            )
        FROM attendance
        ORDER BY subject
    """)

    attendance_data = cursor.fetchall()

    conn.close()

    return render_template(
        "attendance.html",
        attendance_data=attendance_data
    )


# =========================
# NOTICES
# =========================

@app.route(
    "/notices",
    methods=["GET", "POST"]
)
def notices():

    conn = sqlite3.connect("smartcampus.db")
    cursor = conn.cursor()

    if request.method == "POST":

        title = request.form["title"]
        message = request.form["message"]

        date = datetime.now().strftime(
            "%d-%m-%Y"
        )

        cursor.execute("""
            INSERT INTO notices
            (title, message, date)
            VALUES (?, ?, ?)
        """, (
            title,
            message,
            date
        ))

        conn.commit()

    cursor.execute("""
        SELECT *
        FROM notices
        ORDER BY id DESC
    """)

    notices_data = cursor.fetchall()

    conn.close()

    return render_template(
        "notices.html",
        notices=notices_data
    )


# =========================
# AI STUDY SUGGESTIONS
# =========================

@app.route("/ai-suggestions")
def ai_suggestions():

    conn = sqlite3.connect("smartcampus.db")
    cursor = conn.cursor()

    # Count study plans
    cursor.execute("""
        SELECT COUNT(*)
        FROM study_plans
    """)

    study_count = cursor.fetchone()[0]

    # Count assignments
    cursor.execute("""
        SELECT COUNT(*)
        FROM assignments
    """)

    assignment_count = cursor.fetchone()[0]

    # Find next assignment
    cursor.execute("""
        SELECT subject, title, due_date
        FROM assignments
        ORDER BY due_date
        LIMIT 1
    """)

    nearest_assignment = cursor.fetchone()

    # Get attendance records
    cursor.execute("""
        SELECT subject, attended, total
        FROM attendance
    """)

    attendance_records = cursor.fetchall()

    conn.close()

    suggestions = []


    # Study plan suggestion
    if study_count == 0:

        suggestions.append(
            "Create a study plan to organize your daily preparation."
        )

    else:

        suggestions.append(
            f"You currently have {study_count} study plan(s). "
            "Continue following your planned study schedule."
        )


    # Assignment suggestion
    if assignment_count == 0:

        suggestions.append(
            "Add your assignments to SmartCampus "
            "so you can track their due dates."
        )

    else:

        suggestions.append(
            f"You have {assignment_count} assignment(s) recorded."
        )


    # Next assignment suggestion
    if nearest_assignment:

        suggestions.append(
            f"Your next assignment is "
            f"'{nearest_assignment[1]}' "
            f"for {nearest_assignment[0]}, "
            f"due on {nearest_assignment[2]}."
        )


    # Attendance suggestion
    if attendance_records:

        valid_records = [
            record
            for record in attendance_records
            if record[2] > 0
        ]

        if valid_records:

            lowest = min(
                valid_records,
                key=lambda x: x[1] / x[2]
            )

            percentage = (
                lowest[1] /
                lowest[2]
            ) * 100

            suggestions.append(
                f"Pay attention to {lowest[0]}. "
                f"Your current attendance is "
                f"{percentage:.1f}%."
            )

    else:

        suggestions.append(
            "Add your attendance records "
            "to receive attendance-based suggestions."
        )


    # General study suggestions
    suggestions.append(
        "Study for 45–60 minutes and then take a short break."
    )

    suggestions.append(
        "Review difficult subjects regularly "
        "and practice important topics."
    )


    return render_template(
        "ai_suggestions.html",
        suggestions=suggestions
    )


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================
# TEST
# =========================

@app.route("/test")
def test():

    return "SmartCampus is working!"


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":

    init_db()

    app.run(debug=True)