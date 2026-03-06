from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from models import (db, User, Company, Student, PlacementDrive, Application, Admin_role, Company_role, Student_role)
from werkzeug.security import generate_password_hash
from flask_login import LoginManager


app = Flask(__name__)


app.config['SECRET_KEY'] = '123456789'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placeiitm.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def init_db():
    with app.app_context():
        db.create_all()
        admin_user = User.query.filter_by(role=Admin_role).first()
        
        if not admin_user:
            print("No Admin found. Initializing default Admin account...")
            hashed_pw = generate_password_hash('admin123') 
            
            admin = User(
                username='admin',
                email='admin@placeiitm.ac.in', 
                passwd=hashed_pw, 
                role=Admin_role
            )
            
            db.session.add(admin)
            db.session.commit()
            print("Default Admin created, admin@placeiitm.ac.in")

@app.route('/')
def index():
    return "Hello World, Welcome to PlaceIITM"

@app.route('/login')
def login():
    return "THis is login page"
if __name__ == '__main__':
    init_db()
    app.run(debug=True)