from app import db
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    pets = db.relationship('Pet', backref='owner', lazy=True)
    appointments_as_vet = db.relationship('Appointment', backref='veterinario', lazy=True,
                                          foreign_keys='Appointment.vet_id')
    groomings_as_groomer = db.relationship('Grooming', backref='groomer', lazy=True, foreign_keys='Grooming.groomer_id')


class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(100))
    age = db.Column(db.Integer)
    weight = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    appointments = db.relationship('Appointment', backref='pet', lazy=True)
    groomings = db.relationship('Grooming', backref='pet', lazy=True)


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    vet_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(5), nullable=False)
    duration = db.Column(db.Integer, default=30)
    type = db.Column(db.String(50), default='consulta')
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='agendado')
    medical_record = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Grooming(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    groomer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(5), nullable=False)
    duration = db.Column(db.Integer, default=60)
    service_type = db.Column(db.String(50), default='banho e tosa')
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='agendado')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)