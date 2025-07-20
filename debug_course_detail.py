from app import create_app
from app.models import Course, Video, Lesson

app = create_app()

with app.app_context():
    # Test the course detail route logic for course 73
    course_id = 73
    course = Course.query.get_or_404(course_id)
    lessons = Lesson.query.filter_by(course_id=course_id).all()
    videos = Video.query.filter_by(course_id=course_id).all()
    
    print("=== Course Detail Debug ===")
    print(f"Course: {course.title}")
    print(f"Course ID: {course.id}")
    print(f"Number of lessons: {len(lessons)}")
    print(f"Number of videos: {len(videos)}")
    
    print("\n=== Lessons ===")
    for lesson in lessons:
        print(f"- {lesson.title}: {lesson.content[:50]}...")
    
    print("\n=== Videos ===")
    for video in videos:
        print(f"- {video.title}: {video.url}")
    
    # Test the template conditions
    print(f"\n=== Template Conditions ===")
    print(f"lessons exist: {bool(lessons)}")
    print(f"videos exist: {bool(videos)}")
    
    # Test video URL parsing
    for video in videos:
        url = video.url
        print(f"\nVideo URL: {url}")
        
        # Test the YouTube ID extraction logic from template (fixed version)
        youtube_id = None
        if 'youtube.com/embed/' in url:
            youtube_id = url.split('/')[-1].split('?')[0]
        elif 'youtube.com/watch?v=' in url:
            youtube_id = url.split('?v=')[-1].split('&')[0]
        elif 'youtu.be/' in url:
            youtube_id = url.split('/')[-1].split('?')[0]
        
        print(f"Extracted YouTube ID: {youtube_id}")
        print(f"Will show YouTube player: {bool(youtube_id)}")
