from app import create_app, db
from app.models import Course

app = create_app()
with app.app_context():
    courses = [
        Course(title="Data Science 101", description="Intro to data science.", volunteer_id=1),
        Course(title="Machine Learning", description="Basics of ML.", volunteer_id=1),
    ]
    db.session.bulk_save_objects(courses)
    db.session.commit()
    print("Bulk courses loaded.")
