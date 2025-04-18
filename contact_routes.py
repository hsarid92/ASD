from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import db, Contact, Schedule

contact_bp = Blueprint('contact', __name__)

@contact_bp.route('/contacts', methods=['GET', 'POST'])
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
            return redirect(url_for('contact.contacts'))

        # Validate phone number
        if not phone_number.startswith('05') or len(phone_number) != 10 or not phone_number.isdigit():
            flash('Phone number must be 10 digits and start with "05".')
            return redirect(url_for('contact.contacts'))

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

        return redirect(url_for('contact.contacts'))

    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('contacts.html', title="אנשי קשר", contacts=contacts, valid_relations=valid_relations)

@contact_bp.route('/delete_contact/<int:contact_id>', methods=['GET', 'POST'])
@login_required
def delete_contact(contact_id):
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first()
    if not contact:
        flash('Contact not found or you do not have permission to delete it.')
        return redirect(url_for('contact.contacts'))

    if request.method == 'POST':
        if 'confirm' in request.form and request.form['confirm'] == 'yes':
            # Update schedules to remove reference to this contact
            Schedule.query.filter_by(contact_id=contact_id).update({'contact_id': None})
            db.session.delete(contact)
            db.session.commit()
            flash('Contact deleted successfully!')
            return redirect(url_for('contact.contacts'))
        flash('Deletion canceled.')
        return redirect(url_for('contact.contacts'))

    return render_template('confirm_delete.html', title="Confirm Delete", contact=contact)

@contact_bp.route('/contacts_dashboard')
@login_required
def contacts_dashboard():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('contacts_dashboard.html', title="Contacts Dashboard", contacts=contacts)

@contact_bp.route('/contacts_page')
@login_required
def contacts_page():
    contacts = Contact.query.filter_by(user_id=current_user.id).all()
    return render_template('contacts_page.html', title="אנשי קשר", contacts=contacts)
