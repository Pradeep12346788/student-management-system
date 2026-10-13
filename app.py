
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "change-this-for-your-local-project"

DATABASE = "students.db"


# Connect to the database
def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


# Create the students table
def create_table():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            course TEXT NOT NULL,
            marks REAL NOT NULL
        )
    """)

    connection.commit()
    connection.close()


# Display students and search records
@app.route("/")
def index():
    search = request.args.get("search", "").strip()

    connection = get_db_connection()

    if search:
        students = connection.execute(
            """
            SELECT * FROM students
            WHERE name LIKE ? OR email LIKE ?
            ORDER BY id DESC
            """,
            (f"%{search}%", f"%{search}%")
        ).fetchall()
    else:
        students = connection.execute(
            "SELECT * FROM students ORDER BY id DESC"
        ).fetchall()

    connection.close()

    return render_template(
        "index.html",
        students=students,
        search=search
    )


# Add a new student
@app.route("/add", methods=["POST"])
def add_student():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    course = request.form.get("course", "").strip()
    marks_text = request.form.get("marks", "").strip()

    if not name or not email or not course or not marks_text:
        flash("Please fill in every field.", "error")
        return redirect(url_for("index"))

    try:
        marks = float(marks_text)

        if not 0 <= marks <= 100:
            flash("Marks must be between 0 and 100.", "error")
            return redirect(url_for("index"))

    except ValueError:
        flash("Please enter valid numeric marks.", "error")
        return redirect(url_for("index"))

    connection = get_db_connection()

    try:
        connection.execute(
            """
            INSERT INTO students (name, email, course, marks)
            VALUES (?, ?, ?, ?)
            """,
            (name, email, course, marks)
        )
        connection.commit()
        flash("Student added successfully!", "success")

    except sqlite3.IntegrityError:
        flash("This email is already registered.", "error")

    finally:
        connection.close()

    return redirect(url_for("index"))


# Edit an existing student
@app.route("/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    connection = get_db_connection()

    student = connection.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    if student is None:
        connection.close()
        return "Student not found", 404

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        course = request.form.get("course", "").strip()
        marks_text = request.form.get("marks", "").strip()

        if not name or not email or not course or not marks_text:
            flash("Please fill in every field.", "error")
            connection.close()
            return redirect(url_for("edit_student", student_id=student_id))

        try:
            marks = float(marks_text)

            if not 0 <= marks <= 100:
                flash("Marks must be between 0 and 100.", "error")
                connection.close()
                return redirect(url_for("edit_student", student_id=student_id))

        except ValueError:
            flash("Please enter valid numeric marks.", "error")
            connection.close()
            return redirect(url_for("edit_student", student_id=student_id))

        try:
            connection.execute(
                """
                UPDATE students
                SET name = ?, email = ?, course = ?, marks = ?
                WHERE id = ?
                """,
                (name, email, course, marks, student_id)
            )
            connection.commit()
            flash("Student updated successfully!", "success")

        except sqlite3.IntegrityError:
            flash("That email belongs to another student.", "error")
            connection.close()
            return redirect(url_for("edit_student", student_id=student_id))

        connection.close()
        return redirect(url_for("index"))

    connection.close()

    return render_template("edit.html", student=student)


# Delete a student
@app.route("/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    connection = get_db_connection()

    connection.execute(
        "DELETE FROM students WHERE id = ?",
        (student_id,)
    )

    connection.commit()
    connection.close()

    flash("Student deleted successfully!", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    create_table()
    app.run(debug=True)
