from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from app.models import User, Pet, Appointment, Grooming
from app.forms import LoginForm, RegisterForm, ChangePasswordForm, PetForm, AppointmentForm, GroomingForm, \
    MedicalRecordForm
from datetime import datetime, timedelta, time, date
from authlib.integrations.flask_client import OAuth


def init_oauth(app):
    oauth = OAuth(app)
    if app.config['GOOGLE_CLIENT_ID'] and app.config['GOOGLE_CLIENT_SECRET']:
        oauth.register(
            name='google',
            client_id=app.config['GOOGLE_CLIENT_ID'],
            client_secret=app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={'scope': 'openid email profile'}
        )
    return oauth


oauth = None


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def index():
    return render_template('inicio.html')


def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f'Bem-vindo(a), {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        flash('E-mail ou senha inválidos.', 'danger')
    return render_template('formulario.html', form=form, title='Login', submit_text='Entrar')


def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('E-mail já cadastrado.', 'danger')
        else:
            user = User(
                name=form.name.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data),
                role='tutor'
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Cadastro realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
    return render_template('formulario.html', form=form, title='Cadastro', submit_text='Cadastrar')


def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('index'))


@login_required
def dashboard():
    today = date.today()

    if current_user.role == 'admin':
        appointments = Appointment.query.filter_by(status='agendado').filter(Appointment.date >= today).order_by(
            Appointment.date, Appointment.time).all()
        groomings = Grooming.query.filter_by(status='agendado').filter(Grooming.date >= today).order_by(Grooming.date,
                                                                                                        Grooming.time).all()
        past_appointments = Appointment.query.filter(Appointment.date < today).order_by(Appointment.date.desc()).limit(
            10).all()
        past_groomings = Grooming.query.filter(Grooming.date < today).order_by(Grooming.date.desc()).limit(10).all()
    elif current_user.role == 'veterinario':
        appointments = Appointment.query.filter_by(vet_id=current_user.id, status='agendado').filter(
            Appointment.date >= today).order_by(Appointment.date, Appointment.time).all()
        groomings = []
        past_appointments = Appointment.query.filter_by(vet_id=current_user.id).filter(
            Appointment.date < today).order_by(Appointment.date.desc()).limit(10).all()
        past_groomings = []
    elif current_user.role == 'banho_tosa':
        appointments = []
        groomings = Grooming.query.filter_by(groomer_id=current_user.id, status='agendado').filter(
            Grooming.date >= today).order_by(Grooming.date, Grooming.time).all()
        past_appointments = []
        past_groomings = Grooming.query.filter_by(groomer_id=current_user.id).filter(Grooming.date < today).order_by(
            Grooming.date.desc()).limit(10).all()
    else:
        appointments = Appointment.query.join(Pet).filter(Pet.user_id == current_user.id,
                                                          Appointment.status == 'agendado').filter(
            Appointment.date >= today).order_by(Appointment.date, Appointment.time).all()
        groomings = Grooming.query.join(Pet).filter(Pet.user_id == current_user.id,
                                                    Grooming.status == 'agendado').filter(
            Grooming.date >= today).order_by(Grooming.date, Grooming.time).all()
        past_appointments = Appointment.query.join(Pet).filter(Pet.user_id == current_user.id,
                                                               Appointment.date < today).order_by(
            Appointment.date.desc()).limit(10).all()
        past_groomings = Grooming.query.join(Pet).filter(Pet.user_id == current_user.id,
                                                         Grooming.date < today).order_by(Grooming.date.desc()).limit(
            10).all()

    for app in appointments:
        if isinstance(app.date, str):
            app.date = datetime.strptime(app.date, '%Y-%m-%d').date()
    for app in past_appointments:
        if isinstance(app.date, str):
            app.date = datetime.strptime(app.date, '%Y-%m-%d').date()
    for groom in groomings:
        if isinstance(groom.date, str):
            groom.date = datetime.strptime(groom.date, '%Y-%m-%d').date()
    if 'past_groomings' in locals():
        for groom in past_groomings:
            if isinstance(groom.date, str):
                groom.date = datetime.strptime(groom.date, '%Y-%m-%d').date()

    return render_template('painel.html', appointments=appointments, groomings=groomings,
                           past_appointments=past_appointments,
                           past_groomings=past_groomings if 'past_groomings' in locals() else [])


@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if check_password_hash(current_user.password, form.current_password.data):
            current_user.password = generate_password_hash(form.new_password.data)
            db.session.commit()
            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        flash('Senha atual incorreta.', 'danger')
    return render_template('formulario.html', form=form, title='Alterar Senha', submit_text='Alterar')


@login_required
def add_pet():
    if current_user.role != 'tutor':
        flash('Apenas tutores podem cadastrar pets.', 'warning')
        return redirect(url_for('dashboard'))

    form = PetForm()
    if form.validate_on_submit():
        pet = Pet(
            name=form.name.data,
            species=form.species.data,
            breed=form.breed.data,
            age=form.age.data,
            weight=form.weight.data,
            user_id=current_user.id
        )
        db.session.add(pet)
        db.session.commit()
        flash(f'Pet {pet.name} cadastrado com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('formulario.html', form=form, title='Cadastrar Pet', submit_text='Cadastrar')


@login_required
def edit_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    if current_user.role != 'admin' and pet.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))

    form = PetForm(obj=pet)
    if form.validate_on_submit():
        form.populate_obj(pet)
        db.session.commit()
        flash('Pet atualizado com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('formulario.html', form=form, title='Editar Pet', submit_text='Salvar')


@login_required
def delete_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    if current_user.role != 'admin' and pet.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))

    db.session.delete(pet)
    db.session.commit()
    flash('Pet removido com sucesso!', 'success')
    return redirect(url_for('dashboard'))


@login_required
def view_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    if current_user.role != 'admin' and current_user.role != 'veterinario' and pet.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))

    appointments = Appointment.query.filter_by(pet_id=pet_id).order_by(Appointment.date.desc()).all()
    return render_template('pet_detail.html', pet=pet, appointments=appointments)


@login_required
def my_pets():
    if current_user.role != 'tutor':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))

    pets = Pet.query.filter_by(user_id=current_user.id).all()
    return render_template('my_pets.html', pets=pets)


def check_conflict(model, resource_id_field, resource_id, date, time, duration, exclude_id=None):
    start = datetime.combine(date, time)
    end = start + timedelta(minutes=duration)

    query = model.query.filter(
        getattr(model, resource_id_field) == resource_id,
        model.date == date,
        model.status == 'agendado'
    )
    if exclude_id:
        query = query.filter(model.id != exclude_id)

    for item in query.all():
        item_start = datetime.combine(item.date, datetime.strptime(item.time, '%H:%M').time())
        item_end = item_start + timedelta(minutes=item.duration)
        if not (end <= item_start or start >= item_end):
            return True
    return False


def get_duration(appointment_type):
    durations = {
        'consulta': 30,
        'retorno': 30,
        'vacina': 15,
        'banho e tosa': 60,
        'banho': 30,
        'tosa': 30
    }
    return durations.get(appointment_type, 30)


def get_horarios(data_selecionada=None):
    horarios = [('', 'Selecione um horário')]

    hora_atual = None
    if data_selecionada and data_selecionada == datetime.now().date():
        hora_atual = datetime.now().time()

    for hora in range(7, 12):
        for minuto in [0, 30]:
            if hora == 7 and minuto < 30:
                continue
            if hora == 12 and minuto > 0:
                break
            horario_str = f"{hora:02d}:{minuto:02d}"
            if hora_atual:
                horario_time = datetime.strptime(horario_str, '%H:%M').time()
                if horario_time <= hora_atual:
                    continue
            horarios.append((horario_str, horario_str))

    for hora in range(13, 19):
        for minuto in [0, 30]:
            horario_str = f"{hora:02d}:{minuto:02d}"
            if hora_atual:
                horario_time = datetime.strptime(horario_str, '%H:%M').time()
                if horario_time <= hora_atual:
                    continue
            horarios.append((horario_str, horario_str))

    return horarios


@login_required
def get_horarios_api():
    data_str = request.args.get('data')
    if data_str:
        data_selecionada = datetime.strptime(data_str, '%Y-%m-%d').date()
    else:
        data_selecionada = None

    horarios = []

    hora_atual = None
    if data_selecionada and data_selecionada == datetime.now().date():
        hora_atual = datetime.now().time()

    for hora in range(7, 12):
        for minuto in [0, 30]:
            if hora == 7 and minuto < 30:
                continue
            if hora == 12 and minuto > 0:
                break
            horario_str = f"{hora:02d}:{minuto:02d}"
            if hora_atual:
                horario_time = datetime.strptime(horario_str, '%H:%M').time()
                if horario_time <= hora_atual:
                    continue
            horarios.append(horario_str)

    for hora in range(13, 19):
        for minuto in [0, 30]:
            horario_str = f"{hora:02d}:{minuto:02d}"
            if hora_atual:
                horario_time = datetime.strptime(horario_str, '%H:%M').time()
                if horario_time <= hora_atual:
                    continue
            horarios.append(horario_str)

    return jsonify({'horarios': horarios})


@login_required
def new_appointment():
    if current_user.role not in ['tutor', 'admin']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))

    form = AppointmentForm()

    pets = Pet.query.filter_by(user_id=current_user.id).all() if current_user.role == 'tutor' else Pet.query.all()
    form.pet_id.choices = [(0, 'Selecione um pet')] + [(p.id, f'{p.name} ({p.species})') for p in pets]

    vets = User.query.filter_by(role='veterinario').all()
    form.vet_id.choices = [(0, 'Selecione um veterinário')] + [(v.id, f'{v.name}') for v in vets]

    if form.date.data:
        form.time.choices = get_horarios(form.date.data)
    else:
        form.time.choices = get_horarios()

    if form.validate_on_submit():
        if form.pet_id.data == 0:
            flash('Selecione um pet válido.', 'danger')
            return render_template('formulario.html', form=form, title='Nova Consulta', submit_text='Agendar')

        if form.vet_id.data == 0:
            flash('Selecione um veterinário válido.', 'danger')
            return render_template('formulario.html', form=form, title='Nova Consulta', submit_text='Agendar')

        if form.time.data == '':
            flash('Selecione um horário válido.', 'danger')
            return render_template('formulario.html', form=form, title='Nova Consulta', submit_text='Agendar')

        duration = get_duration(form.type.data)
        time_obj = datetime.strptime(form.time.data, '%H:%M').time()

        if check_conflict(Appointment, 'vet_id', form.vet_id.data, form.date.data, time_obj, duration):
            flash('Horário já ocupado para este veterinário.', 'danger')
            return render_template('formulario.html', form=form, title='Nova Consulta', submit_text='Agendar')

        appointment = Appointment(
            pet_id=form.pet_id.data,
            vet_id=form.vet_id.data,
            date=form.date.data,
            time=form.time.data,
            duration=duration,
            type=form.type.data,
            reason=form.reason.data
        )
        db.session.add(appointment)
        db.session.commit()
        flash('Consulta agendada com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('formulario.html', form=form, title='Nova Consulta', submit_text='Agendar')


@login_required
def edit_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    pet = Pet.query.get(appointment.pet_id)

    if current_user.role == 'tutor' and pet.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))

    form = AppointmentForm()

    pets = Pet.query.filter_by(user_id=current_user.id).all() if current_user.role == 'tutor' else Pet.query.all()
    form.pet_id.choices = [(p.id, f'{p.name} ({p.species})') for p in pets]

    vets = User.query.filter_by(role='veterinario').all()
    form.vet_id.choices = [(v.id, f'{v.name}') for v in vets]

    form.time.choices = get_horarios()

    if request.method == 'GET':
        if isinstance(appointment.date, str):
            appointment.date = datetime.strptime(appointment.date, '%Y-%m-%d').date()

        form.pet_id.data = appointment.pet_id
        form.vet_id.data = appointment.vet_id
        form.date.data = appointment.date
        form.time.data = appointment.time
        form.type.data = appointment.type
        form.reason.data = appointment.reason

    if form.validate_on_submit():
        if form.time.data == '':
            flash('Selecione um horário válido.', 'danger')
            return render_template('formulario.html', form=form, title='Editar Consulta', submit_text='Salvar')

        duration = get_duration(form.type.data)
        time_obj = datetime.strptime(form.time.data, '%H:%M').time()

        if check_conflict(Appointment, 'vet_id', form.vet_id.data, form.date.data, time_obj, duration, appointment_id):
            flash('Horário já ocupado para este veterinário.', 'danger')
            return render_template('formulario.html', form=form, title='Editar Consulta', submit_text='Salvar')

        appointment.pet_id = form.pet_id.data
        appointment.vet_id = form.vet_id.data
        appointment.date = form.date.data
        appointment.time = form.time.data
        appointment.duration = duration
        appointment.type = form.type.data
        appointment.reason = form.reason.data

        db.session.commit()
        flash('Consulta atualizada com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('formulario.html', form=form, title='Editar Consulta', submit_text='Salvar')


@login_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    pet = Pet.query.get(appointment.pet_id)

    if current_user.role == 'tutor' and pet.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))

    appointment.status = 'cancelado'
    db.session.commit()
    flash('Consulta cancelada.', 'warning')
    return redirect(url_for('dashboard'))


@login_required
def medical_record(appointment_id):
    if current_user.role != 'veterinario' and current_user.role != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))

    appointment = Appointment.query.get_or_404(appointment_id)
    form = MedicalRecordForm()

    if form.validate_on_submit():
        full_record = f"Diagnóstico: {form.diagnosis.data}\n\nReceita: {form.prescription.data}\n\nObservações: {form.medical_record.data}"
        appointment.medical_record = full_record
        appointment.status = 'realizado'
        db.session.commit()
        flash('Prontuário salvo com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('formulario.html', form=form, title=f'Prontuário - {appointment.pet.name}',
                           submit_text='Salvar')


@login_required
def new_grooming():
    if current_user.role not in ['tutor', 'admin']:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))

    form = GroomingForm()

    pets = Pet.query.filter_by(user_id=current_user.id).all() if current_user.role == 'tutor' else Pet.query.all()
    form.pet_id.choices = [(0, 'Selecione um pet')] + [(p.id, f'{p.name}') for p in pets]

    groomers = User.query.filter_by(role='banho_tosa').all()
    form.groomer_id.choices = [(0, 'Selecione um profissional')] + [(g.id, g.name) for g in groomers]

    if form.date.data:
        form.time.choices = get_horarios(form.date.data)
    else:
        form.time.choices = get_horarios()

    if form.validate_on_submit():
        if form.pet_id.data == 0:
            flash('Selecione um pet válido.', 'danger')
            return render_template('formulario.html', form=form, title='Agendar Banho/Tosa', submit_text='Agendar')

        if form.groomer_id.data == 0:
            flash('Selecione um profissional válido.', 'danger')
            return render_template('formulario.html', form=form, title='Agendar Banho/Tosa', submit_text='Agendar')

        if form.time.data == '':
            flash('Selecione um horário válido.', 'danger')
            return render_template('formulario.html', form=form, title='Agendar Banho/Tosa', submit_text='Agendar')

        duration = get_duration(form.service_type.data)
        time_obj = datetime.strptime(form.time.data, '%H:%M').time()

        if check_conflict(Grooming, 'groomer_id', form.groomer_id.data, form.date.data, time_obj, duration):
            flash('Horário já ocupado para este profissional.', 'danger')
            return render_template('formulario.html', form=form, title='Agendar Banho/Tosa', submit_text='Agendar')

        grooming = Grooming(
            pet_id=form.pet_id.data,
            groomer_id=form.groomer_id.data,
            date=form.date.data,
            time=form.time.data,
            duration=duration,
            service_type=form.service_type.data,
            notes=form.notes.data
        )
        db.session.add(grooming)
        db.session.commit()
        flash('Serviço agendado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('formulario.html', form=form, title='Agendar Banho/Tosa', submit_text='Agendar')


@login_required
def edit_grooming(grooming_id):
    grooming = Grooming.query.get_or_404(grooming_id)
    pet = Pet.query.get(grooming.pet_id)

    if current_user.role == 'tutor' and pet.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))

    form = GroomingForm()

    pets = Pet.query.filter_by(user_id=current_user.id).all() if current_user.role == 'tutor' else Pet.query.all()
    form.pet_id.choices = [(p.id, f'{p.name}') for p in pets]

    groomers = User.query.filter_by(role='banho_tosa').all()
    form.groomer_id.choices = [(g.id, g.name) for g in groomers]

    form.time.choices = get_horarios()

    if request.method == 'GET':
        if isinstance(grooming.date, str):
            grooming.date = datetime.strptime(grooming.date, '%Y-%m-%d').date()

        form.pet_id.data = grooming.pet_id
        form.groomer_id.data = grooming.groomer_id
        form.date.data = grooming.date
        form.time.data = grooming.time
        form.service_type.data = grooming.service_type
        form.notes.data = grooming.notes

    if form.validate_on_submit():
        if form.time.data == '':
            flash('Selecione um horário válido.', 'danger')
            return render_template('formulario.html', form=form, title='Editar Banho/Tosa', submit_text='Salvar')

        duration = get_duration(form.service_type.data)
        time_obj = datetime.strptime(form.time.data, '%H:%M').time()

        if check_conflict(Grooming, 'groomer_id', form.groomer_id.data, form.date.data, time_obj, duration,
                          grooming_id):
            flash('Horário já ocupado para este profissional.', 'danger')
            return render_template('formulario.html', form=form, title='Editar Banho/Tosa', submit_text='Salvar')

        grooming.pet_id = form.pet_id.data
        grooming.groomer_id = form.groomer_id.data
        grooming.date = form.date.data
        grooming.time = form.time.data
        grooming.duration = duration
        grooming.service_type = form.service_type.data
        grooming.notes = form.notes.data

        db.session.commit()
        flash('Serviço atualizado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('formulario.html', form=form, title='Editar Banho/Tosa', submit_text='Salvar')


@login_required
def cancel_grooming(grooming_id):
    grooming = Grooming.query.get_or_404(grooming_id)
    pet = Pet.query.get(grooming.pet_id)

    if current_user.role == 'tutor' and pet.user_id != current_user.id:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))

    grooming.status = 'cancelado'
    db.session.commit()
    flash('Serviço cancelado.', 'warning')
    return redirect(url_for('dashboard'))


@login_required
def history():
    today = date.today()

    if current_user.role == 'admin':
        past_appointments = Appointment.query.filter(Appointment.date < today).order_by(Appointment.date.desc()).all()
        past_groomings = Grooming.query.filter(Grooming.date < today).order_by(Grooming.date.desc()).all()
    elif current_user.role == 'veterinario':
        past_appointments = Appointment.query.filter_by(vet_id=current_user.id).filter(
            Appointment.date < today).order_by(Appointment.date.desc()).all()
        past_groomings = []
    elif current_user.role == 'banho_tosa':
        past_appointments = []
        past_groomings = Grooming.query.filter_by(groomer_id=current_user.id).filter(Grooming.date < today).order_by(
            Grooming.date.desc()).all()
    else:
        past_appointments = Appointment.query.join(Pet).filter(Pet.user_id == current_user.id,
                                                               Appointment.date < today).order_by(
            Appointment.date.desc()).all()
        past_groomings = Grooming.query.join(Pet).filter(Pet.user_id == current_user.id,
                                                         Grooming.date < today).order_by(Grooming.date.desc()).all()

    for app in past_appointments:
        if isinstance(app.date, str):
            app.date = datetime.strptime(app.date, '%Y-%m-%d').date()
    for groom in past_groomings:
        if isinstance(groom.date, str):
            groom.date = datetime.strptime(groom.date, '%Y-%m-%d').date()

    return render_template('history.html', appointments=past_appointments, groomings=past_groomings)


def add_to_calendar(type, item_id):
    from urllib.parse import quote

    if type == 'appointment':
        item = Appointment.query.get_or_404(item_id)
        title = f"Consulta Veterinária - {item.pet.name}"
        description = f"Motivo: {item.reason}\nVeterinário: {item.veterinario.name}"

        if isinstance(item.date, date):
            date_str = item.date.strftime('%Y%m%d')
        else:
            date_str = str(item.date).replace('-', '')

        time_str = item.time.replace(':', '')
        start = f"{date_str}T{time_str}00"

        start_dt = datetime.combine(item.date, datetime.strptime(item.time, '%H:%M').time())
        end_dt = start_dt + timedelta(minutes=item.duration)
        end = f"{date_str}T{end_dt.strftime('%H%M%S')}"

    else:
        item = Grooming.query.get_or_404(item_id)
        title = f"Banho/Tosa - {item.pet.name}"
        description = f"Serviço: {item.service_type}\nObservações: {item.notes or 'Nenhuma'}"

        if isinstance(item.date, date):
            date_str = item.date.strftime('%Y%m%d')
        else:
            date_str = str(item.date).replace('-', '')

        time_str = item.time.replace(':', '')
        start = f"{date_str}T{time_str}00"

        start_dt = datetime.combine(item.date, datetime.strptime(item.time, '%H:%M').time())
        end_dt = start_dt + timedelta(minutes=item.duration)
        end = f"{date_str}T{end_dt.strftime('%H%M%S')}"

    google_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={quote(title)}&dates={start}/{end}&details={quote(description)}"

    return redirect(google_url)


def google_login():
    global oauth
    if oauth is None:
        flash('Login com Google não configurado.', 'warning')
        return redirect(url_for('login'))

    redirect_uri = url_for('google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


def google_callback():
    global oauth
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.parse_id_token(token)

    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        user = User(
            name=user_info['name'],
            email=user_info['email'],
            password=generate_password_hash('oauth_user_' + user_info['sub']),
            role='tutor'
        )
        db.session.add(user)
        db.session.commit()

    login_user(user)
    flash(f'Bem-vindo(a), {user.name}!', 'success')
    return redirect(url_for('dashboard'))