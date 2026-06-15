from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///petcare.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    csrf.init_app(app)

    from app import models, controllers

    with app.app_context():
        db.create_all()

    login_manager.user_loader(controllers.load_user)

    # Rotas principais
    app.add_url_rule('/', 'index', controllers.index)
    app.add_url_rule('/login', 'login', controllers.login, methods=['GET', 'POST'])
    app.add_url_rule('/register', 'register', controllers.register, methods=['GET', 'POST'])
    app.add_url_rule('/logout', 'logout', controllers.logout)
    app.add_url_rule('/dashboard', 'dashboard', controllers.dashboard)
    app.add_url_rule('/change-password', 'change_password', controllers.change_password, methods=['GET', 'POST'])
    app.add_url_rule('/history', 'history', controllers.history)

    # Rotas de pet
    app.add_url_rule('/pet/add', 'add_pet', controllers.add_pet, methods=['GET', 'POST'])
    app.add_url_rule('/pet/edit/<int:pet_id>', 'edit_pet', controllers.edit_pet, methods=['GET', 'POST'])
    app.add_url_rule('/pet/delete/<int:pet_id>', 'delete_pet', controllers.delete_pet)
    app.add_url_rule('/pet/<int:pet_id>', 'view_pet', controllers.view_pet)
    app.add_url_rule('/my-pets', 'my_pets', controllers.my_pets)

    # Rotas de consulta
    app.add_url_rule('/appointment/new', 'new_appointment', controllers.new_appointment, methods=['GET', 'POST'])
    app.add_url_rule('/appointment/edit/<int:appointment_id>', 'edit_appointment', controllers.edit_appointment,
                     methods=['GET', 'POST'])
    app.add_url_rule('/appointment/cancel/<int:appointment_id>', 'cancel_appointment', controllers.cancel_appointment)
    app.add_url_rule('/appointment/medical-record/<int:appointment_id>', 'medical_record', controllers.medical_record,
                     methods=['GET', 'POST'])

    # Rotas de banho/tosa
    app.add_url_rule('/grooming/new', 'new_grooming', controllers.new_grooming, methods=['GET', 'POST'])
    app.add_url_rule('/grooming/edit/<int:grooming_id>', 'edit_grooming', controllers.edit_grooming,
                     methods=['GET', 'POST'])
    app.add_url_rule('/grooming/cancel/<int:grooming_id>', 'cancel_grooming', controllers.cancel_grooming)

    # API de horários
    app.add_url_rule('/get-horarios', 'get_horarios_api', controllers.get_horarios_api)

    # OAuth Google
    app.add_url_rule('/login/google', 'google_login', controllers.google_login)
    app.add_url_rule('/login/google/callback', 'google_callback', controllers.google_callback)

    # Google Calendar
    app.add_url_rule('/calendar/<string:type>/<int:item_id>', 'add_to_calendar', controllers.add_to_calendar)

    return app