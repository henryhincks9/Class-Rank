from flask import Flask
from flask_migrate import Migrate
from models import db
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///data/app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
Migrate(app, db)

if __name__ == '__main__':
    print('Run `flask db` commands with FLASK_APP=manage.py')
