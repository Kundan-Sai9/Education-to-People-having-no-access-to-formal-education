from flask import Blueprint, render_template, request, redirect, url_for, session
from app.models import db, Course, Enrollment, Lesson, LessonProgress, Progress
from app.utils.recommendation import recommend_courses

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
def dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('auth.login'))
    enrollments = (
        Enrollment.query
        .filter_by(student_id=session['user_id'])
        .all()
    )
    return render_template('student_dashboard.html', enrollments=enrollments)

@student_bp.route('/courses')
def courses():
    # This route allows *guests* to browse
    search_query = request.args.get("q")
    class_level = request.args.get("class_level")

    courses = Course.query

    if class_level:
        courses = courses.filter_by(class_level=class_level)

    if search_query:
        courses = courses.filter(Course.title.ilike(f"%{search_query}%"))

    courses = courses.all()

    return render_template('student_courses.html', courses=courses)

@student_bp.route('/home')
def home():
    if session.get("role") != "student":
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    # Get completed courses
    completed = (
        Progress.query
        .filter_by(student_id=user_id)
        .filter(Progress.percent_complete >= 100)
        .all()
    )
    completed_ids = [c.course_id for c in completed]

    # All course IDs
    all_course_ids = [c.id for c in Course.query.all()]

    # Recommended
    recommended_ids = recommend_courses(
        completed_ids=completed_ids,
        all_course_ids=all_course_ids,
        top_n=5
    )

    recommendations = (
        Course.query
        .filter(Course.id.in_(recommended_ids))
        .all()
        if recommended_ids else []
    )

    # Popular courses (top 5 by enrollment count)
    popular_courses = (
        db.session.query(Course)
        .join(Enrollment)
        .group_by(Course.id)
        .order_by(db.func.count(Enrollment.id).desc())
        .limit(5)
        .all()
    )

    return render_template(
        "student_home.html",
        recommendations=recommendations,
        completed_courses=completed,
        popular_courses=popular_courses
    )

@student_bp.route('/enroll/<int:course_id>', methods=['POST'])
def enroll(course_id):
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect(url_for('auth.login'))
    student_id = session['user_id']
    existing = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
    if existing:
        courses = Course.query.all()
        return render_template('student_courses.html', courses=courses, error="You are already enrolled in this course.")
    enrollment = Enrollment(student_id=student_id, course_id=course_id)
    db.session.add(enrollment)
    progress = Progress(student_id=student_id, course_id=course_id, percent_complete=0.0)
    db.session.add(progress)
    db.session.commit()
    return redirect(url_for('student.dashboard'))

@student_bp.route('/course/<int:course_id>')
def course_detail(course_id):
    # Allow guests to view course details
    course = Course.query.get_or_404(course_id)
    lessons = Lesson.query.filter_by(course_id=course_id).all()

    progress = None
    if session.get('role') == 'student':
        progress = Progress.query.filter_by(
            course_id=course_id,
            student_id=session['user_id']
        ).first()

    return render_template(
        'course_detail.html',
        course=course,
        progress=progress,
        lessons=lessons
    )

@student_bp.route('/progress/<int:course_id>/update', methods=['POST'])
def update_progress(course_id):
    if session.get('role') != 'student':
        return redirect(url_for('auth.login'))
    progress = Progress.query.filter_by(course_id=course_id, student_id=session['user_id']).first()
    if progress:
        progress.percent_complete = min(progress.percent_complete + 25.0, 100.0)
        db.session.commit()
    return redirect(url_for('student.course_detail', course_id=course_id))

@student_bp.route('/lesson/<int:lesson_id>/complete', methods=['POST'])
def complete_lesson(lesson_id):
    if session.get('role') != 'student':
        return redirect(url_for('auth.login'))
    progress = LessonProgress.query.filter_by(
        student_id=session['user_id'],
        lesson_id=lesson_id
    ).first()
    if not progress:
        progress = LessonProgress(student_id=session['user_id'], lesson_id=lesson_id, completed=True)
        db.session.add(progress)
    else:
        progress.completed = True
    db.session.commit()

    lesson = Lesson.query.get_or_404(lesson_id)
    course_id = lesson.course_id

    total_lessons = Lesson.query.filter_by(course_id=course_id).count()
    completed_lessons = LessonProgress.query.join(Lesson).filter(
        Lesson.course_id == course_id,
        LessonProgress.student_id == session['user_id'],
        LessonProgress.completed.is_(True)
    ).count()

    percent_complete = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0

    course_progress = Progress.query.filter_by(
        course_id=course_id,
        student_id=session['user_id']
    ).first()
    if course_progress:
        course_progress.percent_complete = percent_complete
    else:
        course_progress = Progress(
            course_id=course_id,
            student_id=session['user_id'],
            percent_complete=percent_complete
        )
        db.session.add(course_progress)
    db.session.commit()

    return redirect(url_for('student.course_detail', course_id=course_id))
