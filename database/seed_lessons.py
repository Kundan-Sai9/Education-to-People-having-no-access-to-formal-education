from app import create_app, db
from app.models import Lesson, Course

app = create_app()
app.app_context().push()

# Clear all existing lessons (optional)
print("🧹 Clearing old lessons...")
Lesson.query.delete()
db.session.commit()

print("🌱 Seeding lessons...")
for course in Course.query.all():
    lessons = [
        Lesson(
            course_id=course.id,
            title="Introduction",
            content="This is the introduction."
        ),
        Lesson(
            course_id=course.id,
            title="Chapter 1",
            content="Content for Chapter 1."
        ),
        Lesson(
            course_id=course.id,
            title="Chapter 2",
            content="Content for Chapter 2."
        ),
        Lesson(
            course_id=course.id,
            title="Review",
            content="Review and wrap-up."
        )
    ]
    db.session.bulk_save_objects(lessons)

db.session.commit()
print("✅ Lessons inserted successfully!")
