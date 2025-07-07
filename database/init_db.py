from app import create_app, db
from app.models import Course, Lesson

app = create_app()
app.app_context().push()

db.create_all()

# OPTIONAL: Seed initial courses/lessons
if not Course.query.first():
    course1 = Course(title="Intro to Learning", description="Basics of learning.")
    db.session.add(course1)
    db.session.commit()

    lessons = [
        Lesson(course_id=course1.id, title="Introduction"),
        Lesson(course_id=course1.id, title="Chapter 1"),
        Lesson(course_id=course1.id, title="Chapter 2"),
        Lesson(course_id=course1.id, title="Review")
    ]
    db.session.bulk_save_objects(lessons)
    db.session.commit()

print("Database initialized.")
