from flask import Blueprint, render_template, request, redirect, url_for, session
from app.models import db, Course, Lesson, Enrollment, Progress, Video, VideoProgress
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

    # Get class filter from query parameters
    class_filter = request.args.get('class_level', type=int)
    
    # Base query for volunteer's courses
    courses_query = Course.query.filter_by(volunteer_id=session['user_id'])
    
    # Apply class filter if provided
    if class_filter:
        courses_query = courses_query.filter_by(class_level=class_filter)
    
    courses = courses_query.all()

    # Attach enrollment and completion counts
    course_data = []
    for course in courses:
        enrollment_count = Enrollment.query.filter_by(course_id=course.id).count()
        completed_count = Progress.query.filter(
            Progress.course_id == course.id,
            Progress.percent_complete >= 100
        ).count()
        
        # Get video and lesson counts
        video_count = Video.query.filter_by(course_id=course.id).count()
        lesson_count = Lesson.query.filter_by(course_id=course.id).count()
        
        course_data.append({
            'course': course,
            'enrollment_count': enrollment_count,
            'completed_count': completed_count,
            'video_count': video_count,
            'lesson_count': lesson_count
        })

    # Get all available class levels for the filter dropdown
    available_classes = db.session.query(Course.class_level).filter_by(
        volunteer_id=session['user_id']
    ).distinct().order_by(Course.class_level).all()
    available_classes = [cls[0] for cls in available_classes]

    return render_template(
        'volunteer_dashboard.html', 
        courses=course_data,
        available_classes=available_classes,
        current_filter=class_filter
    )

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

        # Load existing embeddings (with proper file path)
        embeddings_file = os.path.join(os.path.dirname(__file__), '..', '..', 'course_embeddings.pkl')
        if os.path.exists(embeddings_file):
            with open(embeddings_file, "rb") as f:
                embeddings = pickle.load(f)
        else:
            embeddings = {}

        # Add new embedding
        embeddings[new_course.id] = embedding

        # Save embeddings
        with open(embeddings_file, "wb") as f:
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

@bp.route('/course/<int:course_id>/add_video', methods=['GET', 'POST'])
def add_video(course_id):
    if session.get('role') != 'volunteer':
        return redirect(url_for('auth.login'))

    # Verify the volunteer owns this course
    course = Course.query.filter_by(id=course_id, volunteer_id=session['user_id']).first()
    if not course:
        return redirect(url_for('volunteer.dashboard'))

    if request.method == 'POST':
        title = request.form['title'].strip()
        url = request.form['url'].strip()
        
        # Validate inputs
        if not title or not url:
            return render_template('add_video.html', course=course, 
                                 error="Title and URL are required")
        
        # Convert URL to embed format if needed
        embed_url = convert_to_embed_url(url)
        if not embed_url:
            return render_template('add_video.html', course=course,
                                 error="Invalid video URL. Please provide a valid YouTube, Vimeo, or direct video URL")
        
        try:
            video = Video(title=title, url=embed_url, course_id=course_id)
            db.session.add(video)
            db.session.commit()
            return redirect(url_for('student.course_detail', course_id=course_id))
        except Exception as e:
            db.session.rollback()
            return render_template('add_video.html', course=course,
                                 error=f"Error adding video: {str(e)}")

    return render_template('add_video.html', course=course)

@bp.route('/course/<int:course_id>/manage_videos')
def manage_videos(course_id):
    if session.get('role') != 'volunteer':
        return redirect(url_for('auth.login'))
    
    # Verify the volunteer owns this course
    course = Course.query.filter_by(id=course_id, volunteer_id=session['user_id']).first()
    if not course:
        return redirect(url_for('volunteer.dashboard'))
    
    videos = Video.query.filter_by(course_id=course_id).all()
    return render_template('manage_videos.html', course=course, videos=videos)

@bp.route('/video/<int:video_id>/delete', methods=['POST'])
def delete_video(video_id):
    if session.get('role') != 'volunteer':
        return redirect(url_for('auth.login'))
    
    video = Video.query.get_or_404(video_id)
    
    # Verify the volunteer owns the course this video belongs to
    course = Course.query.filter_by(id=video.course_id, volunteer_id=session['user_id']).first()
    if not course:
        return redirect(url_for('volunteer.dashboard'))
    
    try:
        # Delete associated video progress records first
        VideoProgress.query.filter_by(video_id=video_id).delete()
        
        # Delete the video
        db.session.delete(video)
        db.session.commit()
        
        return redirect(url_for('volunteer.manage_videos', course_id=course.id))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('volunteer.manage_videos', course_id=course.id))

def convert_to_embed_url(url):
    """Convert various video URLs to embed format"""
    import re
    
    # YouTube patterns
    youtube_patterns = [
        r'https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'https?://(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
        r'https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in youtube_patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/embed/{video_id}?enablejsapi=1&rel=0"
    
    # Vimeo patterns
    vimeo_patterns = [
        r'https?://(?:www\.)?vimeo\.com/(\d+)',
        r'https?://player\.vimeo\.com/video/(\d+)',
    ]
    
    for pattern in vimeo_patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            return f"https://player.vimeo.com/video/{video_id}"
    
    # If it's already an embed URL or direct video link, return as is
    if any(domain in url for domain in ['embed', 'player', '.mp4', '.webm', '.ogg']):
        return url
    
    # Invalid URL
    return None

