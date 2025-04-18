from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)

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
    # Removed address and time_with_child fields

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False)  # e.g., "Monday", "Tuesday"
    time_slot = db.Column(db.String(50), nullable=False)  # e.g., "08:00-10:00"
    contact_id = db.Column(db.Integer, db.ForeignKey('contact.id'), nullable=True)  # Store contact ID instead of name
    activity = db.Column(db.String(200), nullable=True)  # New field for free-text activity description
    
    # Removed relation field completely
    
    # Add relationship to Contact model
    contact = db.relationship('Contact', backref='schedules', lazy=True)

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
        survey=survey,  # Pass None if no survey exists
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
    valid_relations = ["מורה", "הורה", "מטפל", "קרוב משפחה", "אחר"]
    if request.method == 'POST':
        contact_id = request.form.get('contact_id')
        name = request.form['name']
        relation = request.form['relation']
        phone_number = request.form['phone_number']

        # Validate relation
        if relation not in valid_relations:
            flash('Invalid relation selected.')
            return redirect(url_for('contacts'))

        # Validate phone number
        if not phone_number.startswith('05') or len(phone_number) != 10 or not phone_number.isdigit():
            flash('Phone number must be 10 digits and start with "05".')
            return redirect(url_for('contacts'))

        if contact_id:  # Edit existing contact
            contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
            if contact:
                contact.name = name
                contact.relation = relation
                contact.phone_number = phone_number
                db.session.commit()
                flash('Contact updated successfully!')
        else:  # Add new contact
            new_contact = Contact(
                user_id=current_user.id,
                name=name,
                relation=relation,
                phone_number=phone_number
            )
            db.session.add(new_contact)
            db.session.commit()
            flash('Contact added successfully!')

        return redirect(url_for('contacts'))

    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('contacts.html', title="אנשי קשר", contacts=contacts, valid_relations=valid_relations)

@app.route('/delete_contact/<int:contact_id>', methods=['GET', 'POST'])
@login_required
def delete_contact(contact_id):
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
    if not contact:
        flash('Contact not found or you do not have permission to delete it.')
        return redirect(url_for('contacts'))

    if request.method == 'POST':
        if 'confirm' in request.form and request.form['confirm'] == 'yes':
            # Update schedules to remove reference to this contact
            Schedule.query.filter_by(contact_id=contact_id).update({'contact_id': None})
            db.session.delete(contact)
            db.session.commit()
            flash('Contact deleted successfully!')
            return redirect(url_for('contacts'))
        flash('Deletion canceled.')
        return redirect(url_for('contacts'))

    return render_template('confirm_delete.html', title="Confirm Delete", contact=contact)

@app.route('/contacts_dashboard')
@login_required
def contacts_dashboard():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('contacts_dashboard.html', title="Contacts Dashboard", contacts=contacts)

@app.route('/contacts_page')
@login_required
def contacts_page():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('contacts_page.html', title="אנשי קשר", contacts=contacts)

@app.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    days_of_week = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]  # Translated to Hebrew
    contacts = Contact.query.filter_by(user_id=current_user.id).all()  # Fetch user contacts
    
    if request.method == 'POST':
        # Debug information
        print("Form data received:", request.form)
        
        selected_days = request.form.getlist('days_of_week')  # Get multiple selected days
        time_slot = request.form.get('time_slot', '')
        contact_id = request.form.get('contact_id')  # Get selected contact ID
        activity = request.form.get('activity', '')  # Get the activity description
        
        print(f"Selected days: {selected_days}")
        print(f"Time slot: {time_slot}")
        print(f"Contact ID: {contact_id}")
        print(f"Activity: {activity}")

        # Validate inputs
        if not selected_days:
            flash('חובה לבחור לפחות יום אחד')
            return redirect(url_for('schedule'))
            
        if not time_slot:
            flash('חובה להזין שעות')
            return redirect(url_for('schedule'))

        # Validate all selected days
        invalid_days = [day for day in selected_days if day not in days_of_week]
        if invalid_days:
            flash(f'ימים לא חוקיים נבחרו: {", ".join(invalid_days)}')
            return redirect(url_for('schedule'))

        # Validate that the contact belongs to the current user if one is selected
        if contact_id and contact_id != '':
            try:
                contact_id = int(contact_id)
                contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
                if not contact:
                    flash('איש קשר לא חוקי נבחר.')
                    return redirect(url_for('schedule'))
            except ValueError:
                flash('מזהה איש קשר לא חוקי.')
                return redirect(url_for('schedule'))
        else:
            contact_id = None

        try:
            # Create a schedule entry for each selected day
            for day in selected_days:
                new_schedule = Schedule(
                    user_id=current_user.id,
                    day_of_week=day,
                    time_slot=time_slot,
                    contact_id=contact_id,
                    activity=activity  # Add the activity field
                )
                db.session.add(new_schedule)
            
            db.session.commit()
            flash(f'נוספו בהצלחה {len(selected_days)} רשומות ללוח הזמנים!')
        except Exception as e:
            db.session.rollback()
            flash(f'שגיאה בהוספת לוח זמנים: {str(e)}')
            print(f"Database error: {str(e)}")
        
        return redirect(url_for('schedule'))

    # Get all schedule entries for the current user
    schedule_entries = Schedule.query.filter_by(user_id=current_user.id).all()
    
    # Extract unique time slots and sort them
    time_slots = sorted(set(entry.time_slot for entry in schedule_entries))
    
    # Create a dictionary for quick lookup of entries by day and time
    schedule_by_day_and_time = {}
    for entry in schedule_entries:
        schedule_by_day_and_time[(entry.day_of_week, entry.time_slot)] = entry
    
    return render_template(
        'schedule.html', 
        title="לוח זמנים", 
        schedule_entries=schedule_entries,
        days_of_week=days_of_week,
        time_slots=time_slots,  # Pass unique time slots
        schedule_by_day_and_time=schedule_by_day_and_time,  # Pass the lookup dictionary
        contacts=contacts,
        rtl=True,
        align_right=True
    )

@app.route('/delete_schedule/<int:schedule_id>', methods=['POST'])
@login_required
def delete_schedule(schedule_id):
    schedule_entry = Schedule.query.filter_by(id=schedule_id, user_id=current_user.id).first()
    if not schedule_entry:
        flash('Schedule entry not found or you do not have permission to delete it.')
        return redirect(url_for('schedule'))

    db.session.delete(schedule_entry)
    db.session.commit()
    flash('Schedule entry deleted successfully!')
    return redirect(url_for('schedule'))

@app.route('/edit_schedule/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
def edit_schedule(schedule_id):
    schedule_entry = Schedule.query.filter_by(id=schedule_id, user_id=current_user.id).first()
    if not schedule_entry:
        flash('Schedule entry not found or you do not have permission to edit it.')
        return redirect(url_for('schedule'))
    
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    days_of_week = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
    
    if request.method == 'POST':
        day_of_week = request.form['day_of_week']
        time_slot = request.form['time_slot']
        contact_id = request.form.get('contact_id')
        activity = request.form.get('activity', '')  # Get activity from form
        
        # Validate inputs
        if not day_of_week or not time_slot:
            flash('Day and time slot are required.')
            return redirect(url_for('edit_schedule', schedule_id=schedule_id))
            
        if day_of_week not in days_of_week:
            flash('Invalid day of the week.')
            return redirect(url_for('edit_schedule', schedule_id=schedule_id))
                
        schedule_entry.day_of_week = day_of_week
        schedule_entry.time_slot = time_slot
        schedule_entry.contact_id = contact_id
        schedule_entry.activity = activity  # Update activity field
        
        db.session.commit()
        flash('Schedule entry updated successfully!')
        return redirect(url_for('schedule'))
        
    return render_template(
        'edit_schedule.html',
        title="עריכת לוח זמנים",
        entry=schedule_entry,
        days_of_week=days_of_week,
        contacts=contacts,
        rtl=True,
        align_right=True
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
