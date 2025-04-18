from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Schedule, Contact
import re
from datetime import datetime

schedule_bp = Blueprint('schedule', __name__)

@schedule_bp.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    days_of_week = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]  # Translated to Hebrew
    
    # Define day range options
    day_ranges = {
        'all_days': {
            'label': 'כל הימים',
            'days': days_of_week
        },
        'sunday_to_thursday': {
            'label': 'ראשון עד חמישי',
            'days': days_of_week[:5]  # First 5 days (Sunday to Thursday)
        }
    }
    
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
            return redirect(url_for('schedule.schedule'))
            
        if not time_slot:
            flash('חובה להזין שעות')
            return redirect(url_for('schedule.schedule'))
            
        # Validate time slot format (HH:MM-HH:MM)
        time_format_pattern = r'^([0-1][0-9]|2[0-3]):([0-5][0-9])-([0-1][0-9]|2[0-3]):([0-5][0-9])$'
        if not re.match(time_format_pattern, time_slot):
            flash('פורמט השעות חייב להיות בתבנית: שעת התחלה: 08:00-שעת סיום: 09:00')
            return redirect(url_for('schedule.schedule'))

        # Validate all selected days
        invalid_days = [day for day in selected_days if day not in days_of_week]
        if invalid_days:
            flash(f'ימים לא חוקיים נבחרו: {", ".join(invalid_days)}')
            return redirect(url_for('schedule.schedule'))

        # Validate that the contact belongs to the current user if one is selected
        if contact_id and contact_id != '':
            try:
                contact_id = int(contact_id)
                contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
                if not contact:
                    flash('איש קשר לא חוקי נבחר.')
                    return redirect(url_for('schedule.schedule'))
            except ValueError:
                flash('מזהה איש קשר לא חוקי.')
                return redirect(url_for('schedule.schedule'))
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
        
        return redirect(url_for('schedule.schedule'))

    # Get all schedule entries for the current user
    schedule_entries = Schedule.query.filter_by(user_id=current_user.id).all()
    
    # Extract unique time slots
    unique_time_slots = set(entry.time_slot for entry in schedule_entries)
    
    # Function to get start time for sorting
    def get_start_time(time_slot):
        start_time_str = time_slot.split('-')[0]
        return datetime.strptime(start_time_str, '%H:%M')
    
    # Sort time slots by start time
    time_slots = sorted(unique_time_slots, key=get_start_time)
    
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
        day_ranges=day_ranges,  # Pass the day ranges
        schedule_by_day_and_time=schedule_by_day_and_time,
        contacts=contacts,
        rtl=True,
        align_right=True
    )

@schedule_bp.route('/delete_schedule/<int:schedule_id>', methods=['POST'])
@login_required
def delete_schedule(schedule_id):
    schedule_entry = Schedule.query.filter_by(id=schedule_id, user_id=current_user.id).first()
    if not schedule_entry:
        flash('Schedule entry not found or you do not have permission to delete it.')
        return redirect(url_for('schedule.schedule'))

    db.session.delete(schedule_entry)
    db.session.commit()
    flash('Schedule entry deleted successfully!')
    return redirect(url_for('schedule.schedule'))

@schedule_bp.route('/edit_schedule/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
def edit_schedule(schedule_id):
    schedule_entry = Schedule.query.filter_by(id=schedule_id, user_id=current_user.id).first()
    if not schedule_entry:
        flash('Schedule entry not found or you do not have permission to edit it.')
        return redirect(url_for('schedule.schedule'))
    
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
            return redirect(url_for('schedule.edit_schedule', schedule_id=schedule_id))
            
        if day_of_week not in days_of_week:
            flash('Invalid day of the week.')
            return redirect(url_for('schedule.edit_schedule', schedule_id=schedule_id))
                
        schedule_entry.day_of_week = day_of_week
        schedule_entry.time_slot = time_slot
        schedule_entry.contact_id = contact_id
        schedule_entry.activity = activity  # Update activity field
        
        db.session.commit()
        flash('Schedule entry updated successfully!')
        return redirect(url_for('schedule.schedule'))
        
    return render_template(
        'edit_schedule.html',
        title="עריכת לוח זמנים",
        entry=schedule_entry,
        days_of_week=days_of_week,
        contacts=contacts,
        rtl=True,
        align_right=True
    )
