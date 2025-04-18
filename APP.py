from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Survey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    child_name = db.Column(db.String(150), nullable=False)
    child_id = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    diagnosis = db.Column(db.String(150), nullable=False)
    diagnosis_age = db.Column(db.Integer, nullable=False)
    educational_framework = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)  # Name of the contact
    relation = db.Column(db.String(50), nullable=False)  # e.g., Teacher, Parent, Therapist
    phone_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    time_with_child = db.Column(db.String(100), nullable=True)  # e.g., "Monday 10:00-12:00"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html', title="Home")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful! Please login.')
        return redirect(url_for('login'))
    return render_template('signup.html', title="Sign Up")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
        return redirect(url_for('login'))
    return render_template('login.html', title="Login")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    survey = Survey.query.filter_by(user_id=current_user.id).first()
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', title="Dashboard", username=current_user.username, survey=survey, contacts=contacts)

@app.route('/survey', methods=['GET', 'POST'])
@login_required
def survey():
    if request.method == 'POST':
        child_name = request.form['child_name']
        child_id = request.form['child_id']
        age = request.form['age']
        gender = request.form['gender']
        diagnosis = request.form['diagnosis']
        diagnosis_age = request.form['diagnosis_age']
        educational_framework = request.form['educational_framework']
        description = request.form['description']

        new_survey = Survey(
            user_id=current_user.id,
            child_name=child_name,
            child_id=child_id,
            age=age,
            gender=gender,
            diagnosis=diagnosis,
            diagnosis_age=diagnosis_age,
            educational_framework=educational_framework,
            description=description
        )
        db.session.add(new_survey)
        db.session.commit()
        flash('Survey submitted successfully!')
        return redirect(url_for('dashboard'))

    return render_template('survey.html', title="Survey")

@app.route('/edit_survey/<int:survey_id>', methods=['GET', 'POST'])
@login_required
def edit_survey(survey_id):
    survey = Survey.query.filter_by(id=survey_id, user_id=current_user.id).first()
    if not survey:
        flash('Survey not found or you do not have permission to edit it.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        survey.child_name = request.form['child_name']
        survey.child_id = request.form['child_id']
        survey.age = request.form['age']
        survey.gender = request.form['gender']
        survey.diagnosis = request.form['diagnosis']
        survey.diagnosis_age = request.form['diagnosis_age']
        survey.educational_framework = request.form['educational_framework']
        survey.description = request.form['description']
        

        db.session.commit()
        flash('Survey updated successfully!')
        return redirect(url_for('dashboard'))

    return render_template('survey.html', title="Edit Survey", survey=survey)

@app.route('/contacts', methods=['GET', 'POST'])
@login_required
def contacts():
    if request.method == 'POST':
        name = request.form['name']
        relation = request.form['relation']
        phone_number = request.form['phone_number']
        address = request.form.get('address', '')
        time_with_child = request.form.get('time_with_child', '')

        new_contact = Contact(
            user_id=current_user.id,
            name=name,
            relation=relation,
            phone_number=phone_number,
            address=address,
            time_with_child=time_with_child
        )
        db.session.add(new_contact)
        db.session.commit()
        flash('Contact added successfully!')
        return redirect(url_for('contacts'))

    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('contacts.html', title="פרטי קשר", contacts=contacts)

@app.route('/edit_contact/<int:contact_id>', methods=['GET', 'POST'])
@login_required
def edit_contact(contact_id):
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
    if not contact:
        flash('Contact not found or you do not have permission to edit it.')
        return redirect(url_for('contacts'))

    if request.method == 'POST':
        contact.name = request.form['name']
        contact.relation = request.form['relation']
        contact.phone_number = request.form['phone_number']
        contact.address = request.form.get('address', '')
        contact.time_with_child = request.form.get('time_with_child', '')

        db.session.commit()
        flash('Contact updated successfully!')
        return redirect(url_for('contacts'))

    return render_template('edit_contact.html', title="ערוך פרטי קשר", contact=contact)

@app.route('/delete_contact/<int:contact_id>', methods=['POST'])
@login_required
def delete_contact(contact_id):
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
    if not contact:
        flash('Contact not found or you do not have permission to delete it.')
        return redirect(url_for('contacts'))

    # Confirm deletion
    if 'confirm' in request.form and request.form['confirm'] == 'yes':
        db.session.delete(contact)
        db.session.commit()
        flash('Contact deleted successfully!')
        return redirect(url_for('contacts'))

    flash('Deletion canceled.')
    return redirect(url_for('edit_contact', contact_id=contact_id))

@app.route('/contacts_dashboard')
@login_required
def contacts_dashboard():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('contacts_dashboard.html', title="Contacts Dashboard", contacts=contacts)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
