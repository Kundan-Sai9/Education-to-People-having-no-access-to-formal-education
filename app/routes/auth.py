from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db, User
import re  # ✅ for password validation

bp = Blueprint('auth', __name__)

@bp.route('/')
def home():
    return render_template('home.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            if user.role == 'student':
                return redirect(url_for('student.dashboard'))
            else:
                return redirect(url_for('volunteer.dashboard'))
        return render_template('login.html', error='Invalid credentials.')
    return render_template('login.html')

def validate_password(password):
    """✅ This function checks your password constraints"""
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return "Password must include at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must include at least one lowercase letter."
    if not re.search(r"\d", password):
        return "Password must include at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must include at least one special character."
    return None

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']
        role = request.form['role']

        # ✅ Check if username already exists
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="Username already exists.")

        # ✅ Validate password constraints
        error = validate_password(password_input)
        if error:
            return render_template('register.html', error=error)

        # ✅ Hash password and create user
        hashed_password = generate_password_hash(password_input)
        user = User(username=username, password=hashed_password, role=role)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
