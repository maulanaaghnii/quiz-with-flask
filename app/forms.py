from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db
from app.models import User
import json
import random
from flask import request

def load_quiz_questions():
    with open('quiz.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        questions = data['quiz']
        # Pilih 5 pertanyaan secara acak
        selected_questions = random.sample(questions, 5)
        # Mengubah kunci 'answer' menjadi 'correct_answer' untuk kompatibilitas
        for q in selected_questions:
            q['correct_answer'] = q.pop('answer')
        return selected_questions

class LoginForm(FlaskForm):
    username = StringField('Nama Pengguna', validators=[DataRequired()])
    password = PasswordField('Kata Sandi', validators=[DataRequired()])
    remember_me = BooleanField('Ingat Saya')
    submit = SubmitField('Masuk')

class RegistrationForm(FlaskForm):
    username = StringField('Nama Pengguna', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Kata Sandi', validators=[DataRequired()])
    password2 = PasswordField(
        'Ulangi Kata Sandi', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Daftar')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError('Nama pengguna sudah digunakan. Silakan gunakan nama pengguna lain.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError('Email sudah digunakan. Silakan gunakan email lain.')
        
class EditProfileForm(FlaskForm):
    username = StringField('Nama Pengguna', validators=[DataRequired()])
    submit = SubmitField('Simpan')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(
                User.username == username.data))
            if user is not None:
                raise ValidationError('Nama pengguna sudah digunakan. Silakan gunakan nama pengguna lain.')

class QuizForm(FlaskForm):
    submit = SubmitField('Kirim Jawaban')

    def __init__(self, questions=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.questions = questions or []

    def get_answers(self):
        answers = {}
        for q in self.questions:
            field_name = f'question_{q["id"]}'
            if field_name in request.form:
                answers[str(q['id'])] = request.form[field_name]
        return answers

    def calculate_score(self):
        score = 0
        correct_answers = 0
        wrong_answers = 0
        for q in self.questions:
            field_name = f'question_{q["id"]}'
            if field_name in request.form:
                user_answer = request.form[field_name]
                correct_answer = q['correct_answer']
                if str(user_answer).strip() == str(correct_answer).strip():
                    score += 2
                    correct_answers += 1
                else:
                    wrong_answers += 1
        return score, correct_answers, wrong_answers

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Kirim Kode Recovery')

class ResetPasswordForm(FlaskForm):
    recovery_code = StringField('Kode Recovery', validators=[DataRequired()])
    password = PasswordField('Password Baru', validators=[DataRequired()])
    password2 = PasswordField('Konfirmasi Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')
    
