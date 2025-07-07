from app import create_app, db
from app.models import Course

app = create_app()
with app.app_context():
    course = Course(title="Intro to Python", description="Learn Python basics.", volunteer_id=1)
    db.session.add(course)
    db.session.commit()
    print("Sample course loaded.")
