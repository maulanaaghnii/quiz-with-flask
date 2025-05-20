from flask import render_template, flash, redirect, url_for, request, session
from app import app
from app.forms import LoginForm, RegistrationForm, EditProfileForm, QuizForm
from flask_login import current_user, login_user, logout_user
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db
from app.models import User, Post, Assessment
from flask_login import login_required
from urllib.parse import urlparse, urljoin, urlsplit
import requests
from datetime import datetime, timedelta
import os
from config import Config

def get_weather_data():
    API_KEY = Config.OPENWEATHERMAP_API_KEY
    if not API_KEY:
        return {
            'today': {'temp': 'N/A', 'description': 'API Key tidak dikonfigurasi'},
            'tomorrow': {'temp': 'N/A', 'description': 'API Key tidak dikonfigurasi'},
            'yesterday': {'temp': 'N/A', 'description': 'API Key tidak dikonfigurasi'}
        }
    
    CITY = 'Jakarta'  # Kota default
    
    try:
        # Data cuaca hari ini
        today_url = f'http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric'
        today_response = requests.get(today_url)
        today_data = today_response.json()
        
        # Data cuaca 5 hari ke depan
        forecast_url = f'http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric'
        forecast_response = requests.get(forecast_url)
        forecast_data = forecast_response.json()
        
        # Validasi response
        if today_response.status_code != 200 or forecast_response.status_code != 200:
            return {
                'today': {'temp': 'N/A', 'description': 'Gagal mengambil data cuaca'},
                'tomorrow': {'temp': 'N/A', 'description': 'Gagal mengambil data cuaca'},
                'yesterday': {'temp': 'N/A', 'description': 'Gagal mengambil data cuaca'}
            }
        
        weather = {
            'today': {
                'temp': round(today_data['main']['temp']),
                'description': today_data['weather'][0]['description']
            },
            'tomorrow': {
                'temp': round(forecast_data['list'][8]['main']['temp']),
                'description': forecast_data['list'][8]['weather'][0]['description']
            },
            'yesterday': {
                'temp': round(forecast_data['list'][0]['main']['temp']),
                'description': forecast_data['list'][0]['weather'][0]['description']
            }
        }
        
        return weather
        
    except Exception as e:
        print(f"Error getting weather data: {str(e)}")
        return {
            'today': {'temp': 'N/A', 'description': 'Terjadi kesalahan'},
            'tomorrow': {'temp': 'N/A', 'description': 'Terjadi kesalahan'},
            'yesterday': {'temp': 'N/A', 'description': 'Terjadi kesalahan'}
        }

@app.route('/')
@app.route('/index')
@login_required
def index():
    # Ambil skor total per user dari tabel Assessment
    scoreboard = db.session.query(
        User.username,
        sa.func.coalesce(sa.func.sum(Assessment.score), 0).label('total_score')
    ).outerjoin(Assessment, Assessment.user_id == User.id).group_by(User.id).order_by(sa.desc('total_score')).all()
    
    # Ambil data cuaca
    weather = get_weather_data()
    
    posts = []
    return render_template('index.html', title='Home Page', posts=posts, scoreboard=scoreboard, weather=weather)

@app.route('/quiz', methods=['GET', 'POST'])
@login_required
def quiz():
    if 'quiz_started' not in session:
        session['quiz_started'] = False
    from app.forms import load_quiz_questions
    if request.method == 'POST' and 'start_quiz' in request.form:
        session['quiz_started'] = True
        session['quiz_questions'] = load_quiz_questions()
        session.modified = True
        return redirect(url_for('quiz'))
    if not session['quiz_started']:
        # Ambil history quiz user
        quiz_history = db.session.query(Assessment).filter_by(user_id=current_user.id).order_by(Assessment.timestamp.desc()).all()
        return render_template('quiz_start.html', title='Start Quiz', quiz_history=quiz_history)
    questions = session.get('quiz_questions', [])
    form = QuizForm(questions=questions)
    if form.validate_on_submit():
        try:
            score, correct_answers, wrong_answers = form.calculate_score()
            assessment = Assessment(
                user_id=current_user.id,
                score=score,
                total_questions=5,
                correct_answers=correct_answers,
                wrong_answers=wrong_answers,
                questions=questions,
                answers=form.get_answers()
            )
            db.session.add(assessment)
            db.session.commit()
            session['quiz_started'] = False
            session.pop('quiz_questions', None)
            return redirect(url_for('quiz'))
        except Exception as e:
            return redirect(url_for('quiz'))
    return render_template('quiz.html', title='Quiz', form=form)

# @app.route('/login')
# def login():
#     form = LoginForm()
#     return render_template('login.html', title='Sign In', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = db.session.scalar(sa.select(User).where(User.username == username))
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('index'))
    posts = db.session.scalars(sa.select(Post).where(Post.user_id == user.id).order_by(Post.timestamp.desc())).all()
    return render_template('user.html', user=user, posts=posts)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
    return render_template('edit_profile.html', title='Edit Profile',
                        form=form)

