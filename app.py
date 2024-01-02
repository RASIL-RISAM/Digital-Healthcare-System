
from flask import Flask,  redirect,render_template,request, session, url_for,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate 
from flask_mail import Mail,Message
from werkzeug.security import generate_password_hash, check_password_hash
from cachetools import LRUCache
import os
import csv
from flask import make_response


app = Flask(__name__)
app.secret_key='pradeep'
app.debug=True
app.config.from_object('config.Config') 
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail=Mail(app)

import secrets
import models


otp_cache = LRUCache(maxsize=100) 
temp_user={}

@app.route('/')
def Home():
	return render_template('./index.html')


@app.route('/signup/patient', methods=['GET', 'POST'])
def patient_signup():
    if request.method == 'POST':
        session['temp_user'] = {
            'username': request.form['username'],
            'email': request.form['email'],
            'phone_number': request.form['phone_number'], 
            'password': request.form['password'],
            'role': 'patient'
        }
        otp = secrets.token_hex(3)  # Generate a 6-character OTP

        # Store the OTP in the session
        session['otp'] = otp

        # Send OTP to the user's email
        msg = Message('OTP Verification', sender='d.pradeep3238@gmail.com', recipients=[session['temp_user']['email']])
        msg.body = f'Your OTP is: {otp}'


        # msg='OTP has been sent to your email. Please verify your email address.'
        # msg='Error sending OTP. Please try again later.'
        try:
            mail.send(msg)
            return redirect(url_for("verify_otp"))
        except Exception as e:

            print(e)
            return redirect(url_for('verify_otp'))

    return render_template("patient_signup.html")


@app.route('/signup/doctor', methods=['GET', 'POST'])
def doctor_signup():
    if request.method == 'POST':
        session['temp_user'] = {
            'username': request.form['username'],
            'email': request.form['email'],
            'phone_number': request.form['phone_number'], 
            'password': request.form['password'],
            'role': 'doctor',
            'speciality': request.form['speciality'],
            'description': request.form['description']
        }
        otp = secrets.token_hex(3)  # Generate a 6-character OTP

        # Store the OTP in the session
        session['otp'] = otp

        # Send OTP to the user's email
        msg = Message('OTP Verification', sender='d.pradeep3238@gmail.com', recipients=[session['temp_user']['email']])
        msg.body = f'Your OTP is: {otp}'

        try:
            mail.send(msg)
            return redirect(url_for("verify_otp"))
        except Exception as e:
            print(e)
            return redirect(url_for('verify_otp'))

    return render_template("doctor_signup.html")


@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        expected_otp = session.get('otp')
        if( entered_otp != expected_otp):
             return render_template('verify_otp.html',msg="Invalid otp")
        else:
            user_data = session.get('temp_user')
            if user_data:
                hashed_password = generate_password_hash(user_data['password'])

                if user_data['role'] == 'patient':
                    user = models.Patient(patient_name=user_data['username'], email=user_data['email'], phone_number = user_data['phone_number'], password=hashed_password)
                elif user_data['role'] == 'doctor':
                    user = models.Doctor(doctor_name=user_data['username'], email=user_data['email'], phone_number = user_data['phone_number'],
                                            password=hashed_password, speciality=user_data.get('speciality'),
                                            profile_description=user_data.get('description'))

                db.session.add(user)
                db.session.commit()

            return redirect(url_for("login"))

    return render_template('verify_otp.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']


        user = None
        if role == 'patient':
            user = models.Patient.query.filter_by(email=email).first()
        elif role == 'doctor':
            user = models.Doctor.query.filter_by(email=email).first()


        if not user:
             return render_template('login.html',msg=" user not found")
        elif user and check_password_hash(user.password, password)==False:   
            return render_template('login.html',msg="wrong password")
        else:
            if role == 'patient':
                session['user_id'] = user.id  # Replace 'user.id' with the actual ID of the logged-in user
                session['user_name']=user.patient_name
                session['user_mail']=user.email
                session['phone_number']=user.phone_number
                session['user_role'] = 'patient' 
                return redirect(url_for('Patient'))
            
            elif role == 'doctor':
                session['user_id'] = user.id  # Replace 'user.id' with the actual ID of the logged-in user
                session['user_name']=user.doctor_name
                session['user_mail']=user.email
                session['user_role'] = 'doctor'  # Or the appropriate role for the user

                return redirect(url_for('Doctor'))

    return render_template('login.html')


@app.route('/logout')
def Logout():
    session.clear()
    return redirect(url_for('Home'))


@app.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    if 'user_id' in session and 'user_role' in session and session['user_role'] == 'patient':
        specialities = db.session.query(models.Doctor.speciality.distinct()).all()
        specialities = [speciality[0] for speciality in specialities]
        patient_name = session.get('user_name')
        patient_email = session['user_mail']
        phone_number=session['phone_number']
        
        doctors = models.Doctor.query.all() 
        if request.method == 'POST':
            doctor_name = request.form['doctor_name']
            health_issue = request.form['health_issue']
            booking_datetime = request.form['datetime']


            appointment=models.Appointment(patient_name=patient_name,patient_email=patient_email,phone_number=phone_number,doctor_name=doctor_name,health_issue=health_issue,appointment_datetime=booking_datetime)
            db.session.add(appointment)
            db.session.commit()


        return render_template('book_appointment.html',specialities=specialities,doctors=doctors,patient_name=patient_name)
    else:
        return "You are not authorized to access this page."

@app.route('/appointments')
def display_appointments():
    if 'user_id' in session and 'user_role' in session and session['user_role'] == 'patient':
        patient_name = session['user_name']
        appointments = models.Appointment.query.filter_by(patient_name=patient_name).all()
        return render_template('my_appointments.html', appointments=appointments)
    else:
        # Handle unauthorized access or display a message
        return "You are not authorized to access this page."

@app.route('/view_appointments')
def view_appointments():
    if 'user_id' in session and 'user_role' in session and session['user_role'] == 'doctor':
        doctor_name = session['user_name']
        appointments = models.Appointment.query.filter_by(doctor_name=doctor_name).all()
        return render_template('view_appointments.html', appointments=appointments)
    else:
        # Handle unauthorized access or display a message
        return "You are not authorized to access this page."

@app.route('/view_doctors')
def view_doctors():
    if 'user_id' in session and 'user_role' in session and session['user_role'] == 'patient':
        doctors = models.Doctor.query.all()
        return render_template('view_doctors.html', doctors=doctors)
    else:
        return "You are not authorized to access this page."

@app.route('/view_patients')
def view_patients():
    if 'user_id' in session and 'user_role' in session and session['user_role'] == 'doctor':
        doctor_name = session['user_name']
        # Query the database for appointments associated with the current doctor
        appointments = models.Appointment.query.filter_by(doctor_name=doctor_name,phone_number=models.Appointment.phone_number).all()

        # Extract unique patient information from appointments
        unique_patients = set()
        for appointment in appointments:
            unique_patients.add((appointment.patient_name, appointment.patient_email,appointment.phone_number))

        # Convert the set of unique patients to a list
        patients = list(unique_patients)

        return render_template('view_patients.html', patients=patients)
    else:
        return "You are not authorized to access this page."



@app.route('/download_reports', methods=['GET'])
def download_reports():
    if 'user_id' in session and 'user_role' in session and session['user_role'] == 'doctor':
        doctor_name = session['user_name']
        selected_date = request.args.get('date')  # Get the selected date from the query parameters

        # Fetch the doctor's appointments for the selected date from the database
        appointments = models.Appointment.query.filter_by(doctor_name=doctor_name, appointment_datetime=selected_date).all()

        if not appointments:
            return "No appointments found for the selected date."


        folder_path = 'doctor_downloads'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_name = f'{doctor_name}_appointments_{selected_date}.csv'
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'w', newline='') as csvfile:
            fieldnames = ['Patient','Health Issue', 'Date & Time', 'Status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for appointment in appointments:
                writer.writerow({
                    'Patient': appointment.patient_name,
                    'Health Issue':appointment.health_issue,
                    'Date & Time': appointment.appointment_datetime,
                    'Status': appointment.status  # Adjust the field name as per your model
                })

        # Create a response to serve the file for download
        response = make_response()
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={file_name}'

        with open(file_path, 'rb') as file:
            response.data = file.read()

        return response

    else:
        # Handle unauthorized access or display a message
        return "You are not authorized to access this page."
    

@app.route('/patient_dashboard')
def Patient():
    if 'user_id' in session and 'user_role' in session and session['user_role'] == 'patient':
        return render_template('./patient_dashboard.html')
    else:
        return "You are not authorized to access this page."

@app.route('/doctor_dashboard')
def Doctor():
    if 'user_id' in session and 'user_role' in session and session['user_role'] == 'doctor':
        doctor_name = session['user_name']
        appointments = models.Appointment.query.filter_by(doctor_name=doctor_name).all()
        return render_template('./doctor_dashboard.html', appointments=appointments)
    else:
        return "You are not authorized to access this page."
    

@app.route('/send_prescription', methods=['POST'])
def send_prescription():
    if 'user_id' in session and 'user_role' in session and session['user_role'] == 'doctor':
        if request.method == 'POST':
            appointment_id = request.json['appointmentId']
            prescription_details = request.json['prescriptionDetails']
            patient_email = request.json['patientEmail']  # Access the patient's email

            # Send the prescription email to the patient
            try:
                msg = Message('Prescription', sender='d.pradeep3238@gmail.com', recipients=[patient_email])
                msg.body = f"Prescription Details:\n\n{prescription_details}"
                mail.send(msg)

                # Update the appointment status in your database
                appointment = models.Appointment.query.get(appointment_id)
                if appointment:
                    appointment.status = 'Completed'
                    db.session.commit()
                    return jsonify({'message': 'Prescription sent and appointment updated.'})
                else:
                    return jsonify({'error': 'Appointment not found.'})
            except Exception as e:
                return jsonify({'error': 'Error sending email.'})
        return jsonify({'message': 'Prescription sent and appointment updated.'})

    return jsonify({'error': 'Unauthorized'})

if __name__ == '__main__':
    app.run()
      