from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.models import db, Course, Enrollment, Lesson, LessonProgress, Progress, Video, VideoProgress
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

@student_bp.route('/course/<int:course_id>/watch')
def watch_course(course_id):
    course = Course.query.get_or_404(course_id)
    videos = Video.query.filter_by(course_id=course_id).all()
    return render_template('watch_course.html', course=course, videos=videos)


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
    videos = Video.query.filter_by(course_id=course_id).all()  # Added videos

    progress = None
    lesson_progress = {}
    video_progress = {}
    
    if session.get('role') == 'student':
        user_id = session['user_id']
        progress = Progress.query.filter_by(
            course_id=course_id,
            student_id=user_id
        ).first()
        
        # Get lesson completion status
        completed_lessons = LessonProgress.query.filter_by(
            student_id=user_id
        ).join(Lesson, LessonProgress.lesson_id == Lesson.id).filter(
            Lesson.course_id == course_id,
            LessonProgress.completed == True
        ).all()
        lesson_progress = {lp.lesson_id: lp.completed for lp in completed_lessons}
        
        # Get video completion status  
        completed_videos = VideoProgress.query.filter_by(
            student_id=user_id
        ).join(Video, VideoProgress.video_id == Video.id).filter(
            Video.course_id == course_id,
            VideoProgress.completed == True
        ).all()
        video_progress = {vp.video_id: vp.completed for vp in completed_videos}

    return render_template(
        'course_detail.html',
        course=course,
        progress=progress,
        lessons=lessons,
        videos=videos,  # Pass videos to template
        lesson_progress=lesson_progress,
        video_progress=video_progress
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
    
    user_id = session['user_id']
    lesson = Lesson.query.get_or_404(lesson_id)
    course_id = lesson.course_id
    
    # Mark lesson as completed
    progress = LessonProgress.query.filter_by(
        student_id=user_id,
        lesson_id=lesson_id
    ).first()
    if not progress:
        progress = LessonProgress(student_id=user_id, lesson_id=lesson_id, completed=True)
        db.session.add(progress)
    else:
        progress.completed = True

    # Calculate progress from videos
    total_videos = Video.query.filter_by(course_id=course_id).count()
    completed_videos = VideoProgress.query.filter_by(
        student_id=user_id
    ).join(Video, VideoProgress.video_id == Video.id).filter(
        Video.course_id == course_id,
        VideoProgress.completed == True
    ).count()
    
    # Calculate progress from lessons
    total_lessons = Lesson.query.filter_by(course_id=course_id).count()
    completed_lessons = LessonProgress.query.filter_by(
        student_id=user_id
    ).join(Lesson, LessonProgress.lesson_id == Lesson.id).filter(
        Lesson.course_id == course_id,
        LessonProgress.completed == True
    ).count()
    
    # Calculate overall progress (considering both videos and lessons)
    total_items = total_videos + total_lessons
    completed_items = completed_videos + completed_lessons
    percent_complete = (completed_items / total_items) * 100 if total_items > 0 else 0

    # Update course progress
    course_progress = Progress.query.filter_by(
        course_id=course_id,
        student_id=user_id
    ).first()
    if course_progress:
        course_progress.percent_complete = percent_complete
    else:
        course_progress = Progress(
            course_id=course_id,
            student_id=user_id,
            percent_complete=percent_complete
        )
        db.session.add(course_progress)
    
    db.session.commit()
    return redirect(url_for('student.course_detail', course_id=course_id))

@student_bp.route('/complete_video/<int:video_id>', methods=['POST'])
def complete_video(video_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    video = Video.query.get_or_404(video_id)
    user_id = session['user_id']

    # Check if already completed
    existing_vp = VideoProgress.query.filter_by(student_id=user_id, video_id=video_id).first()
    if existing_vp and existing_vp.completed:
        # Already completed - return success for AJAX or redirect for form
        if request.content_type == 'application/json' or request.headers.get('Content-Type') == 'application/json':
            return jsonify({
                'success': True, 
                'message': 'Video already completed',
                'progress_percent': get_course_progress_percent(user_id, video.course_id)
            })
        else:
            return redirect(url_for('student.course_detail', course_id=video.course_id))

    # Mark video progress
    if not existing_vp:
        vp = VideoProgress(student_id=user_id, video_id=video_id, completed=True)
        db.session.add(vp)
    else:
        existing_vp.completed = True

    # Update course-level progress based on both videos and lessons
    course_id = video.course_id
    
    # Calculate progress from videos
    total_videos = Video.query.filter_by(course_id=course_id).count()
    completed_videos = VideoProgress.query.filter_by(
        student_id=user_id
    ).join(Video, VideoProgress.video_id == Video.id).filter(
        Video.course_id == course_id,
        VideoProgress.completed == True
    ).count()
    
    # Calculate progress from lessons
    total_lessons = Lesson.query.filter_by(course_id=course_id).count()
    completed_lessons = LessonProgress.query.filter_by(
        student_id=user_id
    ).join(Lesson, LessonProgress.lesson_id == Lesson.id).filter(
        Lesson.course_id == course_id,
        LessonProgress.completed == True
    ).count()
    
    # Calculate overall progress (considering both videos and lessons)
    total_items = total_videos + total_lessons
    completed_items = completed_videos + completed_lessons
    percent = (completed_items / total_items) * 100 if total_items > 0 else 0

    # Update course progress
    progress = Progress.query.filter_by(student_id=user_id, course_id=course_id).first()
    if not progress:
        progress = Progress(student_id=user_id, course_id=course_id, percent_complete=percent)
        db.session.add(progress)
    else:
        progress.percent_complete = percent

    db.session.commit()
    
    # Return appropriate response
    if request.content_type == 'application/json' or request.headers.get('Content-Type') == 'application/json':
        return jsonify({
            'success': True,
            'message': 'Video completed successfully!',
            'progress_percent': percent,
            'completed_videos': completed_videos,
            'total_videos': total_videos,
            'completed_lessons': completed_lessons,
            'total_lessons': total_lessons
        })
    else:
        return redirect(url_for('student.course_detail', course_id=course_id))

def get_course_progress_percent(student_id, course_id):
    """Helper function to get current course progress percentage"""
    progress = Progress.query.filter_by(student_id=student_id, course_id=course_id).first()
    return progress.percent_complete if progress else 0

@student_bp.route('/course/<int:course_id>/progress', methods=['GET'])
def get_course_progress(course_id):
    """API endpoint to get current course progress"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    
    # Get video progress
    total_videos = Video.query.filter_by(course_id=course_id).count()
    completed_videos = VideoProgress.query.filter_by(
        student_id=user_id
    ).join(Video, VideoProgress.video_id == Video.id).filter(
        Video.course_id == course_id,
        VideoProgress.completed == True
    ).count()
    
    # Get lesson progress
    total_lessons = Lesson.query.filter_by(course_id=course_id).count()
    completed_lessons = LessonProgress.query.filter_by(
        student_id=user_id
    ).join(Lesson, LessonProgress.lesson_id == Lesson.id).filter(
        Lesson.course_id == course_id,
        LessonProgress.completed == True
    ).count()
    
    # Calculate overall progress
    total_items = total_videos + total_lessons
    completed_items = completed_videos + completed_lessons
    percent_complete = (completed_items / total_items) * 100 if total_items > 0 else 0
    
    return jsonify({
        'percent_complete': round(percent_complete, 1),
        'completed_videos': completed_videos,
        'total_videos': total_videos,
        'completed_lessons': completed_lessons,
        'total_lessons': total_lessons,
        'completed_items': completed_items,
        'total_items': total_items
    })
