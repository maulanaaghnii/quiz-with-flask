from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta

app = Flask(__name__)
app.config.from_object(Config)
csrf = CSRFProtect(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
login.login_message = None 

def to_wib(dt):
    if dt is None:
        return ""
    wib = dt + timedelta(hours=7)
    return wib.strftime('%Y-%m-%d %H:%M:%S')

app.jinja_env.filters['to_wib'] = to_wib

from app import routes, models, errors