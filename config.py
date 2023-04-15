import os
from flask import Flask, Blueprint
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

basedir = os.path.abspath(os.path.dirname(__file__))

# инициализируем приложения
app = Flask(__name__, template_folder="static/templates")
app.config['SECRET_KEY'] = 'zephyr_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.getcwd()}/static/db/data.db'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

socketio = SocketIO(app, cors_allowed_origins='*')

blueprint = Blueprint(
    'chats_api',
    __name__,
    template_folder='static/templates'
)
