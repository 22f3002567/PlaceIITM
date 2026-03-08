from operator import or_
import os

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from models import (db, User, Company, Student, PlacementDrive, Application, Admin_role, Company_role, Student_role, Pending_status, Approved_status, Rejected_status, Closed_status, Applied_status, Shortlisted_status, Selected_status)
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
    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = PlacementDrive.query.count()
    total_apps = Application.query.count()
    pending_cos = Company.query.filter_by(approval_status=Pending_status).count()
    pending_drives = PlacementDrive.query.filter_by(status=Pending_status).count()
    total_selected = Application.query.filter_by(status=Selected_status).count()
    recent_apps = (Application.query.join(Student).join(PlacementDrive).join(Company).order_by(Application.applied_at.desc()).limit(8).all())

    recent_cos = Company.query.order_by(Company.registered_at.desc()).limit(6).all()
    return render_template('admin_dashboard.html', total_students=total_students, total_companies=total_companies, total_drives=total_drives, total_apps=total_apps, pending_cos=pending_cos, pending_drives=pending_drives, total_selected=total_selected, recent_apps=recent_apps, recent_cos=recent_cos)

@app.route('/admin/companies')
@admin_required
def admin_companies():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()

    query = Company.query
    if search:
        query = query.filter(Company.company_name.ilike(f'%{search}%'))
    if status:
        query = query.filter_by(approval_status=status)
    
    companies = query.order_by(Company.registered_at.desc()).all()
    return render_template('admin_companies.html', companies=companies, search=search, status=status)

@app.route('/admin/companies/<int:co_id>/approve', methods=['POST'])
@admin_required
def admin_company_approve(co_id):
    co = Company.query.get_or_404(co_id)
    co.approval_status = Approved_status
    db.session.commit()
    flash(f"Company '{co.company_name}' approved successfully!", 'success')
    return redirect(url_for('admin_companies'))

@app.route('/admin/companies/<int:co_id>/reject', methods=['POST'])
@admin_required
def admin_company_reject(co_id):
    co = Company.query.get_or_404(co_id)
    co.approval_status = Rejected_status
    db.session.commit()
    flash(f"Company '{co.company_name}' rejected successfully!", 'warning')
    return redirect(url_for('admin_companies'))

@app.route('/admin/companies/<int:co_id>/delete', methods=['POST'])
@admin_required
def admin_company_delete(co_id):
    co = Company.query.get_or_404(co_id)
    db.session.delete(co.user)
    db.session.commit()
    flash(f"Company '{co.company_name}' deleted successfully!", 'danger')
    return redirect(url_for('admin_companies'))

@app.route('/admin/companies/<int:co_id>/blacklist', methods=['POST'])
@admin_required
def admin_toggle_company_blacklist(co_id):
    co = Company.query.get_or_404(co_id)
    co.user.is_blacklisted = not co.user.is_blacklisted
    db.session.commit()
    flash(f"Company '{co.company_name}' blacklisted successfully!", 'info')
    return redirect(url_for('admin_companies'))

@app.route('/admin/companies/<int:co_id>/unblacklist', methods=['POST'])
@admin_required
def admin_toggle_company_unblacklist(co_id):
    co = Company.query.get_or_404(co_id)
    co.user.is_blacklisted = not co.user.is_blacklisted
    db.session.commit()
    flash(f"Company '{co.company_name}' unblacklisted successfully!", 'info')
    return redirect(url_for('admin_companies'))

@app.route('/admin/companies/<int:co_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_company_edit(co_id):
    co = Company.query.get_or_404(co_id)
    if request.method == 'POST':
        co.company_name = request.form.get('company_name', '').strip()
        co.industry = request.form.get('industry', '').strip()
        co.hr_name = request.form.get('hr_name', '').strip()
        co.hr_contact = request.form.get('hr_contact', '').strip()
        co.website = request.form.get('website', '').strip()
        co.description = request.form.get('description', '').strip()
        co.location = request.form.get('location', '').strip()
        db.session.commit()
        flash(f"Company '{co.company_name}' updated successfully!", 'success')
        return redirect(url_for('admin_companies'))
    return render_template('admin_company_edit.html', company=co)

@app.route('/admin/students')
@admin_required
def admin_students():
    search = request.args.get('search', '').strip()
    dept = request.args.get('department', '').strip()
    grad_year = request.args.get('grad_year', '').strip()

    query = Student.query
    if search:
        query = query.filter(or_(
            Student.stu_name.ilike(f'%{search}%'),
            Student.roll_no.ilike(f'%{search}%'),
            Student.email.ilike(f'%{search}%'),
            Student.phone.ilike(f'%{search}%')
            ))
    if dept:
        query = query.filter_by(department=dept)
    if grad_year:
        query = query.filter_by(grad_year=grad_year)
    
    students = query.order_by(Student.registered_at.desc()).all()
    return render_template('admin_students.html', students=students, search=search, dept=dept, grad_year=grad_year)


@app.route('/admin/students/<int:stu_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_student_edit(stu_id):
    stu = Student.query.get_or_404(stu_id)
    if request.method == 'POST':
        grad_yr = request.form.get('grad_year', '').strip()
        cgpa_str = request.form.get('cgpa', '').strip()
        stu.stu_name = request.form.get('stu_name', '').strip()
        stu.phone = request.form.get('phone', '').strip()
        stu.department = request.form.get('department', '').strip()
        stu.grad_year = int(grad_yr) if grad_yr.isdigit() else None
        stu.cgpa = float(cgpa_str) if cgpa_str.replace('.','',1).isdigit() else None
        stu.skills = request.form.get('skills', '').strip()
        stu.roll_no = request.form.get('roll_no', '').strip()
        stu.email = request.form.get('email', '').strip()
         
        db.session.commit()
        flash(f"Student '{stu.stu_name}' updated successfully!", 'success')
        return redirect(url_for('admin_students'))
    return render_template('admin_student_edit.html', student=stu)

@app.route('/admin/students/<int:stu_id>/delete', methods=['POST'])
@admin_required
def admin_student_delete(stu_id):
    stu = Student.query.get_or_404(stu_id)
    db.session.delete(stu.user)
    db.session.commit()
    flash(f"Student '{stu.stu_name}' deleted successfully!", 'danger')
    return redirect(url_for('admin_students'))

@app.route('/admin/students/<int:stu_id>/blacklist', methods=['POST'])
@admin_required
def admin_student_blacklist(stu_id):
    stu = Student.query.get_or_404(stu_id)
    stu.user.is_blacklisted = not stu.user.is_blacklisted
    db.session.commit()
    flash(f"Student '{stu.stu_name}' blacklisted successfully!", 'warning')
    return redirect(url_for('admin_students'))

@app.route('/admin/students/<int:stu_id>/unblacklist', methods=['POST'])
@admin_required
def admin_student_unblacklist(stu_id):
    stu = Student.query.get_or_404(stu_id)
    stu.user.is_blacklisted = not stu.user.is_blacklisted
    db.session.commit()
    flash(f"Student '{stu.stu_name}' unblacklisted successfully!", 'success')
    return redirect(url_for('admin_students'))


@app.route('/admin/drives')
@admin_required
def admin_drives():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()

    query = PlacementDrive.query.join(Company)
    if search:
        query = query.filter(PlacementDrive.job_title.ilike(f'%{search}%') | Company.company_name.ilike(f'%{search}%'))
    if status:
        query = query.filter_by(status=status)
    
    drives = query.order_by(PlacementDrive.created_at.desc()).all()
    return render_template('admin_drives.html', drives=drives, search=search, status_filter=status)

@app.route('/admin/drives/<int:drive_id>/approve', methods=['POST'])
@admin_required
def admin_drive_approve(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = Approved_status
    db.session.commit()
    flash(f"Placement drive '{drive.job_title}' approved successfully!", 'success')
    return redirect(url_for('admin_drives'))

@app.route('/admin/drives/<int:drive_id>/reject', methods=['POST'])
@admin_required
def admin_drive_reject(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = Rejected_status
    db.session.commit()
    flash(f"Placement drive '{drive.job_title}' rejected successfully!", 'warning')
    return redirect(url_for('admin_drives'))

@app.route('/admin/drives/<int:drive_id>/close', methods=['POST'])
@admin_required
def admin_drive_close(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.status = Closed_status
    db.session.commit()
    flash(f"Placement drive '{drive.job_title}' closed successfully!", 'info')
    return redirect(url_for('admin_drives'))

@app.route('/admin/applications', methods=['POST'])
@admin_required
def admin_applications():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    query = Application.query.join(Student).join(PlacementDrive).join(Company)
    if search:
        query = query.filter(or_(
            Student.stu_name.ilike(f'%{search}%'),
            Student.roll_no.ilike(f'%{search}%'),
            Student.email.ilike(f'%{search}%'),
            Student.phone.ilike(f'%{search}%'),
            PlacementDrive.job_title.ilike(f'%{search}%'),
            Company.company_name.ilike(f'%{search}%')
        ))
    if status:
        query = query.filter_by(Application.status==status)
    applications = query.order_by(Application.applied_on.desc()).all()
    return render_template('admin_applications.html', applications=applications, search=search, status_filter=status)

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