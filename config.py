import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# инициализируем приложения
app = Flask(__name__, template_folder="static/templates")
app.config['SECRET_KEY'] = 'zephyr_secret_key'
file_path = os.path.abspath(os.getcwd())+"/static/db/data.db"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + file_path

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
