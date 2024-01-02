from app import db  
from sqlalchemy import Enum

class Patient(db.Model):
    __tablename__ = 'patient'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_name = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(15), unique=True)  
    password = db.Column(db.String(1000), nullable=False)

class Doctor(db.Model):
    __tablename__='doctor'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    doctor_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    phone_number = db.Column(db.String(15), unique=True)  
    password = db.Column(db.String(1000), nullable=False)
    profile_description = db.Column(db.Text)
    speciality = db.Column(db.String(20), nullable=False)
    contact = db.Column(db.String(15),unique=True)


class Appointment(db.Model):
    __tablename__='appointment'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    patient_name  = db.Column(db.String(25))
    patient_email =db.Column(db.String(200))
    phone_number = db.Column(db.String(15)) 
    doctor_name = db.Column(db.String(25))
    health_issue = db.Column(db.String(100))
    appointment_datetime = db.Column(db.DateTime, nullable=False)
    status = db.Column(Enum('Pending', 'Completed'),default='Pending') 


class Prescription(db.Model):
    __tablename__ = 'prescription'
    
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    patient_name = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_name = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date_prescribed = db.Column(db.DateTime, nullable=False)
    medication_name = db.Column(db.String(100), nullable=False)
    dosage_instructions = db.Column(db.Text, nullable=False)