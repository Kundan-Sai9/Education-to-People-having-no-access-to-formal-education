import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Course, Lesson, User, Video, VideoProgress, LessonProgress, Progress, Enrollment

def recreate_database():
    """Recreate the database with all current models"""
    app = create_app()
    
    with app.app_context():
        print("Dropping all existing tables...")
        db.drop_all()
        
        print("Creating all tables with current models...")
        db.create_all()
        
        print("Database schema updated successfully!")
        
        # Optional: Seed comprehensive data based on existing seed files
        if not User.query.first():
            from werkzeug.security import generate_password_hash
            
            # Create multiple users for testing
            users_data = [
                {"username": "volunteer1", "password": "password123", "role": "volunteer"},
                {"username": "volunteer2", "password": "password123", "role": "volunteer"},
                {"username": "student1", "password": "password123", "role": "student"},
                {"username": "student2", "password": "password123", "role": "student"},
            ]
            
            for user_data in users_data:
                user = User(
                    username=user_data["username"], 
                    password=generate_password_hash(user_data["password"]),
                    role=user_data["role"]
                )
                db.session.add(user)
            
            db.session.commit()
            print("Default users created (2 volunteers, 2 students).")
        
        # Create comprehensive courses for all class levels (1-12)
        if not Course.query.first():
            # Subject definitions from your seed_data.py
            subjects = [
                {"title": "Mathematics", "description": "Learn numbers, operations, algebra, geometry, and advanced mathematical concepts."},
                {"title": "Science", "description": "Explore physics, chemistry, biology, and the natural world around us."},
                {"title": "English", "description": "Develop reading, writing, grammar, literature, and communication skills."},
                {"title": "Social Studies", "description": "Understand history, geography, civics, and cultural studies."},
                {"title": "Computer Science", "description": "Learn programming, algorithms, and digital literacy skills."},
                {"title": "Art & Creativity", "description": "Explore visual arts, music, and creative expression."},
            ]
            
            # Create courses for classes 1–12
            courses_created = []
            for level in range(1, 13):
                for subject in subjects:
                    course = Course(
                        title=f"{subject['title']} - Class {level}",
                        description=f"Class {level}: {subject['description']}",
                        class_level=level,
                        volunteer_id=1  # Assign to volunteer1
                    )
                    db.session.add(course)
                    courses_created.append(course)
            
            db.session.commit()
            print(f"Created {len(courses_created)} courses for classes 1-12.")
            
            # Add lessons for each course (from your seed_lessons.py logic)
            print("Adding lessons to all courses...")
            lesson_templates = [
                {"title": "Introduction", "content": "Welcome to this subject! In this introductory lesson, we'll explore the fundamentals and set the foundation for your learning journey."},
                {"title": "Fundamentals", "content": "Let's dive into the core concepts and basic principles that form the building blocks of this subject."},
                {"title": "Practical Applications", "content": "Now we'll see how these concepts apply in real-world scenarios and practice with hands-on examples."},
                {"title": "Advanced Topics", "content": "Building on our foundation, we'll explore more complex ideas and advanced applications."},
                {"title": "Review & Assessment", "content": "Let's review what we've learned and test your understanding with exercises and assessments."}
            ]
            
            for course in courses_created:
                for i, lesson_template in enumerate(lesson_templates, 1):
                    lesson = Lesson(
                        course_id=course.id,
                        title=f"Lesson {i}: {lesson_template['title']}",
                        content=lesson_template['content']
                    )
                    db.session.add(lesson)
            
            db.session.commit()
            print(f"Added {len(lesson_templates)} lessons to each course.")
            
            # Add sample videos for some courses
            print("Adding sample educational videos...")
            sample_videos = [
                {"title": "Introduction to the Subject", "url": "https://www.youtube.com/embed/dQw4w9WgXcQ?enablejsapi=1&origin=http://127.0.0.1:5000"},
                {"title": "Key Concepts Explained", "url": "https://www.youtube.com/embed/9bZkp7q19f0?enablejsapi=1&origin=http://127.0.0.1:5000"},
                {"title": "Practical Examples", "url": "https://www.youtube.com/embed/fJ9rUzIMcZQ?enablejsapi=1&origin=http://127.0.0.1:5000"},
            ]
            
            # Add videos to first few courses as examples
            for i, course in enumerate(courses_created[:6]):  # Add to first 6 courses
                for video_template in sample_videos:
                    video = Video(
                        course_id=course.id,
                        title=f"{course.title}: {video_template['title']}",
                        url=video_template['url']
                    )
                    db.session.add(video)
            
            db.session.commit()
            print("Sample videos added to first 6 courses.")
        
        print("Database initialization completed successfully!")

if __name__ == "__main__":
    recreate_database()
