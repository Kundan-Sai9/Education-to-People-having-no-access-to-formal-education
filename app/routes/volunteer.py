from flask import Blueprint, render_template, request, redirect, url_for, session
from app.models import db, Course, Lesson
from sentence_transformers import SentenceTransformer
import pickle
import os

bp = Blueprint('volunteer', __name__, url_prefix='/volunteer')

# Load model (you can move this to a separate utils.py if you prefer)
model = SentenceTransformer("all-MiniLM-L6-v2")


@bp.route('/dashboard')
def dashboard():
    if session.get('role') != 'volunteer':
        return redirect(url_for('auth.login'))

    courses = Course.query.filter_by(volunteer_id=session['user_id']).all()

    # Attach enrollment and completion counts
    course_data = []
    for course in courses:
        enrollment_count = Enrollment.query.filter_by(course_id=course.id).count()
        completed_count = Progress.query.filter(
            Progress.course_id == course.id,
            Progress.percent_complete >= 100
        ).count()
        course_data.append({
            'course': course,
            'enrollment_count': enrollment_count,
            'completed_count': completed_count
        })

    return render_template('volunteer_dashboard.html', courses=course_data)

@bp.route("/create", methods=["GET", "POST"])
def create():
    if session.get("role") != "volunteer":
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        class_level = request.form["class_level"]

        # Create course in DB
        new_course = Course(
            title=title,
            description=description,
            class_level=class_level,
            volunteer_id=session["user_id"]
        )
        db.session.add(new_course)
        db.session.flush()  # Assigns new_course.id without committing yet

        # Create default lessons
        default_lessons = [
            Lesson(
                course_id=new_course.id,
                title="Introduction",
                content="This is the introduction."
            ),
            Lesson(
                course_id=new_course.id,
                title="Chapter 1",
                content="Content for Chapter 1."
            ),
            Lesson(
                course_id=new_course.id,
                title="Chapter 2",
                content="Content for Chapter 2."
            ),
            Lesson(
                course_id=new_course.id,
                title="Review",
                content="Review and wrap-up."
            )
        ]
        db.session.bulk_save_objects(default_lessons)
        db.session.flush()

        # Encode embedding
        text = f"{title}. {description}"
        embedding = model.encode(text)

        # Load existing embeddings
        if os.path.exists("course_embeddings.pkl"):
            with open("course_embeddings.pkl", "rb") as f:
                embeddings = pickle.load(f)
        else:
            embeddings = {}

        # Add new embedding
        embeddings[new_course.id] = embedding

        # Save embeddings
        with open("course_embeddings.pkl", "wb") as f:
            pickle.dump(embeddings, f)

        db.session.commit()  # Commit everything together

        return redirect(url_for("volunteer.dashboard"))

    return render_template("volunteer_create.html")


@bp.route('/course/<int:course_id>/add_lesson', methods=['GET', 'POST'])
def add_lesson(course_id):
    if session.get('role') != 'volunteer':
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        lesson = Lesson(title=title, content=content, course_id=course_id)
        db.session.add(lesson)
        db.session.commit()
        return redirect(url_for('volunteer.dashboard'))

    return render_template('add_lesson.html')
