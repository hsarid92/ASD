from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Survey

survey_bp = Blueprint('survey', __name__)

@survey_bp.route('/survey', methods=['GET', 'POST'])
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
        return redirect(url_for('user.dashboard'))

    return render_template('survey.html', title="Survey")

@survey_bp.route('/edit_survey/<int:survey_id>', methods=['GET', 'POST'])
@login_required
def edit_survey(survey_id):
    survey = Survey.query.filter_by(id=survey_id, user_id=current_user.id).first()
    if not survey:
        flash('Survey not found or you do not have permission to edit it.')
        return redirect(url_for('user.dashboard'))

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
        return redirect(url_for('user.dashboard'))

    return render_template('survey.html', title="Edit Survey", survey=survey)
