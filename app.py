import os

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from models import (db, User, Company, Student, PlacementDrive, Application, Admin_role, Company_role, Student_role)
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

app = Flask(__name__)


app.config['SECRET_KEY'] = '123456789'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placeiitm.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(
    os.path.dirname(__file__), 'static', 'uploads', 'resumes'
)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 

db.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Hey Seeker, Pleasee log in to access this page."
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




def init_db():
    with app.app_context():
        db.create_all()
        
        if not User.query.filter_by(role=Admin_role).first():
            print("No Admin found. Initializing default Admin account...")
            hashed_pw = generate_password_hash('Siddharth@123') 
            
            admin_user = User(
                username='siddharth_admin',
                email='siddharth@placeiitm.ac.in', 
                passwd=hashed_pw, 
                role=Admin_role,
                is_blacklisted=False
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin created, siddharth@placeiitm.ac.in/Siddharth@123")
        else:
            print("Admin account already exists. Skipping initialization.")


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin():
            flash('Acces denied - Admins allowed only.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated

def company_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_company():
            flash('Access denied - Companies allowed only.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated

def student_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_student():
            flash('Access denied - Students allowed only.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated

def redirect_dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    elif current_user.is_company():
        return redirect(url_for('company_dashboard'))
    elif current_user.is_student():
        return redirect(url_for('student_dashboard'))
    else:
        flash("Invalid user role. Contact support.", 'danger')
        logout_user()
        return redirect(url_for('login'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        passwd = request.form.get('password', '')
        role = request.form.get('role', '')

        if not all([email, passwd, role]):
            flash("Hey Seeker,Please fill in all fields including role..", 'warning')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.passwd, passwd):
            flash("Heyy Seeker, Invalid credentials. Please try again..", 'danger')
            return redirect(url_for('login'))
        
        if user.role != role:
            flash(f"Hey Seeker, You selected {role} but your account is {user.role}. Please select the correct role.", 'warning')
            return redirect(url_for('login'))
        login_user(user)
        flash(f"Welcome back, {user.username}! You have successfully logged in as {user.role}.", 'success')
        return redirect_dashboard()
    return render_template('login.html')


@app.route('/register/company', methods=['GET', 'POST'])
def reg_company():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        passwd = request.form.get('password', '')
        confirm_passwd = request.form.get('confirm_password', '')
        company_name = request.form.get('company_name', '').strip()
        industry = request.form.get('industry', '').strip()
        hr_name = request.form.get('hr_name', '').strip()
        hr_contact = request.form.get('hr_contact', '').strip()
        website = request.form.get('website', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()

        if not all([username, email, passwd, confirm_passwd, company_name]):
            flash("Please fill in all required fields (*).", 'warning')
            return render_template('reg_company.html', form=request.form, industries="Industries")
        

        if passwd != confirm_passwd:
            flash("Passwords do not match..", 'warning')
            return render_template('reg_company.html', form=request.form, industries="Industries")

        user = User(
            username=username,
            email=email,
            passwd=generate_password_hash(passwd),
            role=Company_role
        )
        db.session.add(user)
        db.session.flush()

        company = Company(
            user_id=user.id,
            company_name=company_name,
            industry=industry,
            hr_name=hr_name,
            hr_contact=hr_contact,
            website=website,
            description=description,
            location=location
        )
        db.session.add(company)
        db.session.commit()
        flash("Company registration successfully Submitted! Your account is pending approval by the Placement Cell.", 'success')
        return redirect(url_for('login'))
        
        
    return render_template('reg_company.html', form={}, industries="Industries")

@app.route('/register/student', methods=['GET', 'POST'])
def reg_student():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        passwd = request.form.get('password', '')
        confirm_passwd = request.form.get('confirm_password', '')
        stu_name = request.form.get('stu_name', '').strip() 
        phone = request.form.get('phone', '').strip()
        roll_no = request.form.get('roll_no', '').strip()
        dept = request.form.get('department', '').strip()
        degree = request.form.get('degree', '').strip()
        grad_year = request.form.get('grad_year', '').strip()
        cgpa = request.form.get('cgpa', '').strip()
        skills = request.form.get('skills', '').strip()

        if not all([username, email, passwd, confirm_passwd, stu_name, roll_no]):
            flash("Please fill in all required fields (*).", 'warning')
            return render_template('reg_student.html', form=request.form)
        if passwd != confirm_passwd:
            flash("Passwords do not match..", 'warning')
            return render_template('reg_student.html', form=request.form)
        
        user = User(
            username=username,
            email=email,
            passwd=generate_password_hash(passwd),
            role=Student_role
        )
        db.session.add(user)
        db.session.flush()
        

        student = Student(
            user_id=user.id,
            stu_name=stu_name,
            email=email,
            phone=phone,
            roll_no=roll_no,
            department=dept,
            degree=degree,
            grad_year=int(grad_year) if grad_year.isdigit() else None,
            cgpa=float(cgpa) if cgpa.replace('.','',1).isdigit() else None,
            skilss=skills,
            resume_filename= resume_filename
        )
        db.session.add(student)
        db.session.commit()
        flash("Student registration successfully Submitted! Please Login", 'success')
        return redirect(url_for('login'))

    return render_template('reg_student.html', form={})

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return "This is Admin Dashboard - Under Construction"

@app.route('/company/dashboard')
@company_required
def company_dashboard():
    return "This is Company Dashboard - Under Construction"

@app.route('/student/dashboard')
@student_required
def student_dashboard():
    return "This is Student Dashboard - Under Construction"


if __name__ == '__main__':
    init_db()
    app.run(debug=True)