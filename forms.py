from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SelectField, TextAreaField, IntegerField, FloatField, \
    DateField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, ValidationError
from datetime import datetime


class LoginForm(FlaskForm):
    email = EmailField('E-mail',
                       validators=[DataRequired(message='E-mail é obrigatório'), Email(message='E-mail inválido')])
    password = PasswordField('Senha', validators=[DataRequired(message='Senha é obrigatória')])
    submit = SubmitField('Entrar')


class RegisterForm(FlaskForm):
    name = StringField('Nome completo', validators=[DataRequired(message='Nome é obrigatório'), Length(min=3, max=100,
                                                                                                       message='Nome deve ter entre 3 e 100 caracteres')])
    email = EmailField('E-mail',
                       validators=[DataRequired(message='E-mail é obrigatório'), Email(message='E-mail inválido')])
    password = PasswordField('Senha', validators=[DataRequired(message='Senha é obrigatória'),
                                                  Length(min=6, message='Senha deve ter no mínimo 6 caracteres')])
    confirm_password = PasswordField('Confirmar senha',
                                     validators=[DataRequired(message='Confirmação de senha é obrigatória'),
                                                 EqualTo('password', message='As senhas não conferem')])
    submit = SubmitField('Cadastrar')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Senha atual', validators=[DataRequired(message='Senha atual é obrigatória')])
    new_password = PasswordField('Nova senha', validators=[DataRequired(message='Nova senha é obrigatória'),
                                                           Length(min=6,
                                                                  message='Nova senha deve ter no mínimo 6 caracteres')])
    confirm_password = PasswordField('Confirmar nova senha',
                                     validators=[DataRequired(message='Confirmação é obrigatória'),
                                                 EqualTo('new_password', message='As senhas não conferem')])
    submit = SubmitField('Alterar senha')


class PetForm(FlaskForm):
    name = StringField('Nome do pet', validators=[DataRequired(message='Nome do pet é obrigatório')])
    species = SelectField('Espécie', choices=[('Cachorro', 'Cachorro'), ('Gato', 'Gato'), ('Outro', 'Outro')],
                          validators=[DataRequired(message='Selecione uma espécie')])
    breed = StringField('Raça')
    age = IntegerField('Idade (anos)',
                       validators=[NumberRange(min=0, max=30, message='Idade deve estar entre 0 e 30 anos')])
    weight = FloatField('Peso (kg)',
                        validators=[NumberRange(min=0, max=100, message='Peso deve estar entre 0 e 100 kg')])
    submit = SubmitField('Salvar')


class AppointmentForm(FlaskForm):
    pet_id = SelectField('Pet', coerce=int, choices=[], validators=[DataRequired(message='Selecione um pet')])
    vet_id = SelectField('Veterinário', coerce=int, choices=[],
                         validators=[DataRequired(message='Selecione um veterinário')])
    date = DateField('Data', validators=[DataRequired(message='Selecione uma data')])
    time = SelectField('Horário', choices=[], validators=[DataRequired(message='Selecione um horário')])
    type = SelectField('Tipo', choices=[
        ('', 'Selecione um tipo'),
        ('consulta', 'Consulta (30 min)'),
        ('vacina', 'Vacina (15 min)'),
        ('retorno', 'Retorno (30 min)')
    ], validators=[DataRequired(message='Selecione um tipo de consulta')])
    reason = TextAreaField('Motivo')
    submit = SubmitField('Agendar')

    def validate_date(self, field):
        if field.data.weekday() == 6:
            raise ValidationError('Não atendemos aos domingos. Escolha de segunda a sábado.')

        if field.data < datetime.now().date():
            raise ValidationError('Não é possível agendar em datas passadas.')


class GroomingForm(FlaskForm):
    pet_id = SelectField('Pet', coerce=int, choices=[], validators=[DataRequired(message='Selecione um pet')])
    groomer_id = SelectField('Profissional', coerce=int, choices=[],
                             validators=[DataRequired(message='Selecione um profissional')])
    date = DateField('Data', validators=[DataRequired(message='Selecione uma data')])
    time = SelectField('Horário', choices=[], validators=[DataRequired(message='Selecione um horário')])
    service_type = SelectField('Serviço', choices=[
        ('', 'Selecione um serviço'),
        ('banho e tosa', 'Banho e Tosa (1 hora)'),
        ('banho', 'Banho (30 min)'),
        ('tosa', 'Tosa (30 min)')
    ], validators=[DataRequired(message='Selecione um tipo de serviço')])
    notes = TextAreaField('Observações')
    submit = SubmitField('Agendar')

    def validate_date(self, field):
        if field.data.weekday() == 6:
            raise ValidationError('Não atendemos aos domingos. Escolha de segunda a sábado.')

        if field.data < datetime.now().date():
            raise ValidationError('Não é possível agendar em datas passadas.')


class MedicalRecordForm(FlaskForm):
    medical_record = TextAreaField('Observações', validators=[DataRequired(message='Observações são obrigatórias')])
    diagnosis = TextAreaField('Diagnóstico')
    prescription = TextAreaField('Receita')
    submit = SubmitField('Salvar')