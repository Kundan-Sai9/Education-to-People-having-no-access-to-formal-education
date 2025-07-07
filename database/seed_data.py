
from app import create_app, db
from app.models import Course, User

app = create_app()

courses = [
    {"title": "Mathematics", "description": "Learn numbers and operations."},
    {"title": "Science", "description": "Explore the natural world."},
    {"title": "English", "description": "Develop reading and writing skills."},
    {"title": "Social Studies", "description": "Understand society and culture."},
]

def seed_courses():
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Create a test volunteer
        volunteer = User(username="volunteer1", password="test", role="volunteer")
        db.session.add(volunteer)
        db.session.commit()

        # Add courses for classes 1–12
        for level in range(1, 13):
            for base in courses:
                course = Course(
                    title=f"{base['title']} - Class {level}",
                    description=base["description"],
                    class_level=level,
                    volunteer_id=volunteer.id
                )
                db.session.add(course)

        db.session.commit()
        print("✅ Seeded courses for classes 1–12.")

if __name__ == "__main__":
    seed_courses()
