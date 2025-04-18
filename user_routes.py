from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

user_bp = Blueprint('user', __name__)

@user_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('user.signup'))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful! Please login.')
        return redirect(url_for('user.login'))
    return render_template('signup.html', title="Sign Up")

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('user.dashboard'))
        flash('Invalid username or password')
        return redirect(url_for('user.login'))
    return render_template('login.html', title="Login")

@user_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@user_bp.route('/dashboard')
@login_required
def dashboard():
    from models import Survey
    survey = Survey.query.filter_by(user_id=current_user.id).first()
    
    # Translate gender, diagnosis, and educational framework to Hebrew
    if survey:
        gender_translation = {'Male': 'זכר', 'Female': 'נקבה'}
        diagnosis_translation = {'Autism': 'אוטיזם', 'Other': 'אחר'}
        framework_translation = {'Mainstream': 'חינוך רגיל'}
        
        survey.gender = gender_translation.get(survey.gender, survey.gender)
        survey.diagnosis = diagnosis_translation.get(survey.diagnosis, survey.diagnosis)
        survey.educational_framework = framework_translation.get(survey.educational_framework, survey.educational_framework)
    
    return render_template(
        'dashboard.html', 
        title="לוח בקרה", 
        username=current_user.username, 
        survey=survey,
        labels={
            'child_name': 'שם הילד',
            'child_id': 'תעודת זהות',
            'age': 'גיל',
            'gender': 'מין',
            'diagnosis': 'אבחנה',
            'diagnosis_age': 'גיל באבחנה',
            'educational_framework': 'מסגרת חינוכית',
            'description': 'תיאור'
        }
    )
