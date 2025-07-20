from app import create_app, db
from app.models import Course, Lesson, User, Video, VideoProgress, LessonProgress, Progress, Enrollment

app = create_app()
app.app_context().push()

# Drop all tables and recreate them (this ensures all new models are included)
db.drop_all()
db.create_all()

print("All tables dropped and recreated successfully.")

# OPTIONAL: Seed initial data
if not User.query.first():
    # Create a default volunteer user
    from werkzeug.security import generate_password_hash
    volunteer_user = User(
        username="volunteer1", 
        password=generate_password_hash("password123"),
        role="volunteer"
    )
    db.session.add(volunteer_user)
    db.session.commit()
    print("Default volunteer user created.")

# OPTIONAL: Seed initial courses/lessons
if not Course.query.first():
    course1 = Course(
        title="Intro to Learning", 
        description="Basics of learning and education fundamentals.",
        class_level=1,
        volunteer_id=1  # Reference the volunteer user we just created
    )
    db.session.add(course1)
    db.session.commit()
    print("Sample course created.")

    lessons = [
        Lesson(course_id=course1.id, title="Introduction", content="Welcome to this learning journey. In this introduction, we'll cover the basics of effective learning."),
        Lesson(course_id=course1.id, title="Chapter 1: Learning Fundamentals", content="Understanding how learning works and the key principles of effective study."),
        Lesson(course_id=course1.id, title="Chapter 2: Memory and Retention", content="Techniques for improving memory and retaining information long-term."),
        Lesson(course_id=course1.id, title="Review and Summary", content="Review of key concepts and practical applications of what we've learned.")
    ]
    db.session.bulk_save_objects(lessons)
    db.session.commit()
    print("Sample lessons created.")

    # Add some sample videos
    videos = [
        Video(course_id=course1.id, title="Introduction Video", url="https://www.youtube.com/embed/dQw4w9WgXcQ"),
        Video(course_id=course1.id, title="Learning Fundamentals Video", url="https://www.youtube.com/embed/dQw4w9WgXcQ")
    ]
    db.session.bulk_save_objects(videos)
    db.session.commit()
    print("Sample videos created.")

print("Database initialization completed successfully!")
