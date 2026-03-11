from datetime import datetime, date
from sqlalchemy import or_, func
import os, io, base64

from flask import Flask, render_template, request, redirect, url_for, flash, abort, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from models import (db,
                     User, Company, Student, PlacementDrive, Application,
                     Admin_role, Company_role, Student_role, Pending_status, Approved_status, Rejected_status, Closed_status, 
                     Applied_status, Shortlisted_status, Selected_status, Rejected_app,
                     App_statuses, Departments, Degrees, Industries, Job_types )
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)

app.config['SECRET_KEY'] = 'placeiitm_secret_sidd'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placeiitm.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(
    os.path.dirname(__file__), 'static', 'uploads', 'resumes'
)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER']) 

db.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Hey Seeker, Pleasee log in to access this page."
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



ALLOWED_EXT = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def safe_float(s):
    """Return float(s) clamped to 0 - 10 , or None on bad input.."""
    try:
        v = float(s)
        return v if 0 <= v <= 10 else None
    except (ValueError, TypeError):
        return None


def init_db():
    with app.app_context():
        db.create_all()
        
        if not User.query.filter_by(role=Admin_role).first():
            print("No Admin found. Initializing default Admin account...")
            hashed_pw = generate_password_hash(
                'Siddharth@300', method='pbkdf2:sha256', salt_length=8
                ) 
            
            admin_user = User(
                username='siddharth_admin',
                email='siddharth@placeiitm.ac.in', 
                passwd=hashed_pw, 
                role=Admin_role,
                is_blacklisted=False
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin created, siddharth@placeiitm.ac.in/Siddharth@300")
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
    

NAVY  = "#1D3360"
GOLD  = "#D7B555"
GREEN = "#20C28C"
RED   = "#E74E4E"
BLUE  = "#3982F7"
AMBER = "#ED9E16"
GREY  = "#A8AFBB"


def chart(data, chart_type='bar', title='Chart', xlabel='X', ylabel='Y', colors=None):
    if not data or all(v == 0 for v in data.values()):
        return None
    palette    = colors or [NAVY, GOLD, GREEN, RED, BLUE, AMBER, GREY]
    plt.rcParams['font.family'] = 'DejaVu Sans'
    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor('#FFFFFF')
    ax.set_facecolor('#F8FAFC')
    keys       = list(data.keys())
    vals       = list(data.values())
    bar_colors = [palette[i % len(palette)] for i in range(len(keys))]

    if chart_type == 'pie':
        wedges, texts, autos = ax.pie(
            vals, labels=keys, autopct='%1.1f%%',
            colors=bar_colors, startangle=140,
            wedgeprops=dict(edgecolor='white', linewidth=2)
        )
        for t in texts: t.set_fontsize(10)
        for a in autos: a.set_fontsize(9); a.set_color('white'); a.set_fontweight('bold')

    elif chart_type == 'bar':
        bars = ax.bar(keys, vals, color=bar_colors, edgecolor='white', linewidth=1.5, width=0.55)
        ax.set_xlabel(xlabel, fontsize=10, color='#4A5568')
        ax.set_ylabel(ylabel, fontsize=10, color='#4A5568')
        ax.yaxis.grid(True, linestyle='--', alpha=0.5, color="#C4D1DF")
        ax.set_axisbelow(True)
        ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
        if vals: ax.set_yticks(range(0, max(int(max(vals)) + 2, 2)))
        for b in bars:
            h = b.get_height()
            if h > 0:
                ax.annotate(str(int(h)),
                    xy=(b.get_x() + b.get_width() / 2, h),
                    xytext=(0, 4), textcoords='offset points',
                    ha='center', fontsize=9, fontweight='bold', color=NAVY)

    if title:
        ax.set_title(title, fontsize=13, fontweight='bold', color=NAVY, pad=12)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=110, bbox_inches='tight')
    buf.seek(0)
    result = base64.b64encode(buf.getvalue()).decode()
    plt.close(fig)
    return result



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_dashboard()
    
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
            flash(f"Hey Seeker, You selected {role} but your account is {user.role.title()}. Please select the correct role.", 'warning')
            return redirect(url_for('login'))

        if not user.is_active:
            flash("Hey sir, Your account is deactivated, Please contact admin..", 'danger')
            return redirect(url_for('login')) 

        if user.is_blacklisted:
            flash("Your accountt has been blacklistedd.. Please Contact to the placement cell..", 'danger')
            return redirect(url_for('login'))   
        
        login_user(user)
        flash(f"Welcome back, {user.username}! You have successfully logged in as {user.role}..", 'success')
        return redirect_dashboard()
    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sir, You have been logged out..", 'info')
    return redirect(url_for('index'))


@app.route('/register/company', methods=['GET', 'POST'])
def reg_company():
    if current_user.is_authenticated:
        return redirect_dashboard()
    
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
            return render_template('reg_company.html', form=request.form, industries=Industries)
        

        if passwd != confirm_passwd:
            flash("Passwords do not match..", 'warning')
            return render_template('reg_company.html', form=request.form, industries=Industries)

        if len(passwd) < 6:
            flash("Password must be at least 6 chars..", "warning")
            return render_template('reg_company.html', form=request.form, industries=Industries)           

        try:

            user = User(
                username=username,
                email=email,
                passwd=generate_password_hash(passwd, method='pbkdf2:sha256', salt_length=8),
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
        
        except IntegrityError as e:
            db.session.rollback()
            err = str(e.orig)
            if 'email' in err:
                flash("This email is already registered..", 'warning')
            elif 'username' in err:
                flash("This email is already registered..", 'warning')
            
            else:
                flash("Registration failed.. Please try again..", 'danger')
            return render_template('reg_company.html', form={}, industries=Industries)
            
    return render_template('reg_company.html', form={}, industries=Industries)

@app.route('/register/student', methods=['GET', 'POST'])
def reg_student():
    if current_user.is_authenticated:
        return redirect_dashboard()
    
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
            return render_template('reg_student.html', form=request.form, departments=Departments, degrees=Degrees)
        if passwd != confirm_passwd:
            flash("Passwords do not match..", 'warning')
            return render_template('reg_student.html', form=request.form, departments=Departments, degrees=Degrees)
        
        if len(passwd) < 6:
            flash("Passward must be at least 6 chars..", 'warning')
            return render_template('reg_student.html', form=request.form, departments=Departments, degrees=Degrees)
        
        resume_filename = None
        if 'resume' in request.files:
            f = request.files['resume']
            if f and f.filename and allowed_file(f.filename):
                resume_filename = secure_filename(
                    email.replace('@', "_").replace('.', '_') + '_resume.pdf'
                )
                f.save(os.path.join(app.config["UPLOAD_FOLDER"], resume_filename))
                
        try:
            user = User(
                username=username,
                email=email,
                passwd=generate_password_hash(passwd, method='pbkdf2:sha256', salt_length=8),
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
                cgpa=safe_float(cgpa),
                skills=skills,
                resume_filename= resume_filename
            )
            db.session.add(student)
            db.session.commit()
            flash("Student registration successfully Submitted! Please Login", 'success')
            return redirect(url_for('login'))
        except IntegrityError as e:
            db.session.rollback()
            err = str(e.orig)
            if 'email' in err:
                flash("This email is already registered.", 'warning')
            elif 'roll_no' in err:
                flash("This roll number is already registered.", 'warning')
            elif 'username' in err:
                flash("This username is already taken.", 'warning')
            else:
                flash("Registration failed. Please try again.", 'danger')
            return render_template('reg_student.html', form=request.form, departments=Departments, degrees=Degrees)
        
    return render_template('reg_student.html', form={}, departments=Departments, degrees=Degrees)

@app.route('/resume/<filename>')
@login_required
def serve_resume(filename):
    safe = secure_filename(filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'], safe)

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
    recent_apps = (Application.query.join(Student, Application.student_id == Student.id)
                   .join(PlacementDrive, Application.drive_id == PlacementDrive.id)
                   .join(Company, PlacementDrive.company_id == Company.id)
                   .order_by(Application.applied_at.desc()).limit(8).all())

    recent_cos = Company.query.order_by(Company.registered_at.desc()).limit(6).all()
    
    app_status_data = {s: c for s, c in (
        db.session.query(Application.status, func.count(Application.id))
        .group_by(Application.status).all()
    )}
    app_chart = chart(app_status_data, 'pie', 'Application Status',
                      colors=[BLUE, AMBER, GREEN, RED])

    drive_data = {
        'Pending':  PlacementDrive.query.filter_by(status=Pending_status).count(),
        'Approved': PlacementDrive.query.filter_by(status=Approved_status).count(),
        'Rejected': PlacementDrive.query.filter_by(status=Rejected_status).count(),
        'Closed':   PlacementDrive.query.filter_by(status=Closed_status).count(),
    }
    drive_chart = chart(drive_data, 'bar', 'Drives by Status',
                        xlabel='Status', ylabel='Count',
                        colors=[AMBER, GREEN, RED, GREY])
    
    return render_template('admin_dashboard.html', total_students=total_students, total_companies=total_companies, total_drives=total_drives, total_apps=total_apps, pending_cos=pending_cos, pending_drives=pending_drives, total_selected=total_selected, recent_apps=recent_apps, recent_cos=recent_cos, app_chart=app_chart, drive_chart=drive_chart)

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
    return render_template('admin_companies.html', companies=companies, search=search, status_filter=status)

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
    action = 'blacklisted' if co.user.is_blacklisted else 'unblacklisted'
    flash(f"Company '{co.company_name}' {action} successfully!", 'info')
    return redirect(url_for('admin_companies'))

@app.route('/admin/companies/<int:co_id>/unblacklist', methods=['POST'])
@admin_required
def admin_toggle_company_unblacklist(co_id):
    co = Company.query.get_or_404(co_id)
    co.user.is_blacklisted = not co.user.is_blacklisted
    db.session.commit()
    action = 'unblacklisted' if not co.user.is_blacklisted else 'blacklisted'
    flash(f"Company '{co.company_name}' {action} successfully!", 'info')
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
    return render_template('admin_edit_company.html', company=co, industries=Industries)

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
    return render_template('admin_students.html', students=students, search=search, dept=dept, grad_year=grad_year, departments=Departments)


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
        stu.degree = request.form.get('degree', '').strip()
        stu.grad_year = int(grad_yr) if grad_yr.isdigit() else None
        stu.cgpa = safe_float(cgpa_str)
        stu.skills = request.form.get('skills', '').strip()
        stu.bio = request.form.get('bio', '').strip()
        stu.roll_no = request.form.get('roll_no', '').strip()
         
        db.session.commit()
        flash(f"Student '{stu.stu_name}' updated successfully!", 'success')
        return redirect(url_for('admin_students'))
    return render_template('admin_edit_student.html', student=stu, departments=Departments, degrees=Degrees)

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
    action = "blacklisted" if stu.user.is_blacklisted else "unblacklisted"
    flash(f"Student '{stu.stu_name}' {action} successfully!", 'warning')
    return redirect(url_for('admin_students'))

@app.route('/admin/students/<int:stu_id>/unblacklist', methods=['POST'])
@admin_required
def admin_student_unblacklist(stu_id):
    stu = Student.query.get_or_404(stu_id)
    stu.user.is_blacklisted = not stu.user.is_blacklisted
    db.session.commit()
    action = 'unblacklisted' if not stu.user.is_blacklisted else 'blacklisted'
    flash(f"Student '{stu.stu_name}' {action} successfully!", 'success')
    return redirect(url_for('admin_students'))


@app.route('/admin/drives')
@admin_required
def admin_drives():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()

    query = PlacementDrive.query.join(Company)
    if search:
        query = query.filter(or_(
            PlacementDrive.job_title.ilike(f'%{search}%'),
            Company.company_name.ilike(f'%{search}%')
        ))
    if status:
        query = query.filter(PlacementDrive.status == status)
    
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

@app.route('/admin/applications')
@admin_required
def admin_applications():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    query = (Application.query
             .join(Student, Application.student_id == Student.id)
             .join(PlacementDrive, Application.drive_id == PlacementDrive.id)
             .join(Company, PlacementDrive.company_id == Company.id))
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
        query = query.filter(Application.status == status)
    applications = query.order_by(Application.applied_at.desc()).all()
    return render_template('admin_applications.html', applications=applications, search=search, status_filter=status, app_statuses=App_statuses)

@app.route('/company/dashboard')
@company_required
def company_dashboard():
    co = current_user.company_profile
    if not co:
        flash("Company profile not found. Contact Admin Please..", 'danger')
        return redirect(url_for('index'))
    
    drives = (PlacementDrive.query
              .filter_by(company_id=co.id)
              .order_by(PlacementDrive.created_at.desc()).all()
              )
    total_drives = len(drives)
    active_drives = sum(1 for d in drives if d.status == Approved_status)
    Pending_drives = sum(1 for d in drives if d.status == Pending_status)
    Closed_drives = sum(1 for d in drives if d.status == Closed_status)
    total_apps = sum(len(d.applications) for d in drives)
    total_selected = (Application.query
                      .join(PlacementDrive, Application.drive_id == PlacementDrive.id)
                      .filter(PlacementDrive.company_id == co.id,
                               Application.status == Selected_status)
                      .count())
    
    chart_data = {
        (d.job_title[:18] + '...' if len(d.job_title) > 18 else d.job_title): len(d.applications)
        for d in drives if d.applications
    }
    app_chart = chart(chart_data, 'bar', 'Applicants per Drive',
                      xlabel='Drive', ylabel='Count',
                      colors=[NAVY, GOLD, GREEN, BLUE, AMBER, RED])

    return render_template('company_dashboard.html', company=co, drives=drives, total_drives=total_drives, active_drives=active_drives, pending_drives=Pending_drives, closed_drives=Closed_drives, total_apps=total_apps, total_selected=total_selected, app_chart=app_chart)

@app.route('/company/drives/create', methods=['GET', 'POST'])
@company_required
def company_create_drive():
    co = current_user.company_profile
    if not co or not co.is_approved():
        flash("Hey, your company must be admin-approved before posting drives.. Contact Admin Please..", 'danger')
        return redirect(url_for('company_dashboard'))
    
    if request.method == 'POST':
        job_title = request.form.get('job_title', '').strip()
        job_desc = request.form.get('job_desp', '').strip()
        eligibility = request.form.get('eligible_criteria', '').strip()
        req_skills = request.form.get('req_skills', '').strip()
        salary = request.form.get('salary_range', '').strip()
        job_type = request.form.get('job_type', '').strip()
        location = request.form.get('location', '').strip()
        deadline_str = request.form.get('application_deadline', '').strip()

        if not job_title or not job_desc or not deadline_str:
            flash("Job title, description and application deadline are required fields..", 'warning')
            return render_template('company_create_drive.html', form=request.form, job_types=Job_types)
        
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.", 'warning')
            return render_template('company_create_drive.html', form=request.form, job_types=Job_types)
        
        if deadline < date.today():
            flash("Deadline can not bee in the past..", "warning")
            return render_template('company_create_drive.html', form=request.form, job_types=Job_types)
        drive = PlacementDrive(
            company_id=co.id,
            job_title=job_title,
            job_desp=job_desc,
            eligible_criteria=eligibility,
            req_skills=req_skills,
            salary_range=salary,
            job_type=job_type,
            location=location,
            appication_deadline=deadline,
            status=Pending_status
        )
        db.session.add(drive)
        db.session.commit()
        flash("Placement drive created successfully! It is pending admin approval.", 'success')
        return redirect(url_for('company_dashboard'))
    return render_template('company_create_drive.html', form={}, job_types=Job_types)




@app.route('/company/drives/<int:drive_id>/edit', methods=['GET', 'POST'])
@company_required
def company_edit_drive(drive_id):
    co = current_user.company_profile
    drive = PlacementDrive.query.filter_by(id=drive_id, company_id=co.id).first_or_404()

    if drive.status not in (Pending_status, Rejected_status):
        flash("Only pending or rejected drives can be edited..", 'warning')
        return redirect(url_for('company_dashboard'))
    
    if request.method == "POST":
        deadline_str = request.form.get("application_deadline", '').strip()
        if not deadline_str:
            flash("wait a minute sir, Deadline is required..", 'warning')
            return render_template('company_edit_drive.html', drive=drive, form=request.form, job_types=Job_types)
        
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Please select a valid date.", 'warning')
            return render_template('company_edit_drive.html', drive=drive,
                                   form=request.form, job_types=Job_types)

        if deadline < date.today():
            flash("Deadline cannot be in the past.", 'warning')
            return render_template('company_edit_drive.html', drive=drive,
                                   form=request.form, job_types=Job_types)
        
        drive.job_title = request.form.get('job_title', '').strip()
        drive.job_desp = request.form.get('job_desp', '').strip()
        drive.eligible_criteria = request.form.get('eligible_criteria', '').strip()
        drive.req_skills = request.form.get('req_skills', '').strip()
        drive.salary_range = request.form.get('salary_range', '').strip()
        drive.job_type = request.form.get('job_type', '').strip()
        drive.location = request.form.get('location', '').strip()
        drive.appication_deadline = deadline
        drive.status = Pending_status
        db.session.commit()
        flash("Drive updated and re-submitted for admin approval..", 'success')
        return redirect(url_for('company_dashboard'))
    
    return render_template('company_edit_drive.html', drive=drive, form={}, job_types=Job_types)

@app.route('/company/drives/<int:drive_id>/close', methods=["POST"])
@company_required
def company_close_drive(drive_id):
    co = current_user.company_profile
    drive = PlacementDrive.query.filter_by(id= drive_id, company_id= co.id).first_or_404()
    drive.status = Closed_status
    db.session.commit()
    flash("Drive Closed..", 'info')
    return redirect(url_for('company_dashboard'))



@app.route('/company/drives/<int:drive_id>/delete', methods=['POST'])
@company_required
def company_delete_drive(drive_id):
    co    = current_user.company_profile
    drive = PlacementDrive.query.filter_by(id=drive_id, company_id=co.id).first_or_404()
    db.session.delete(drive)
    db.session.commit()
    flash('Drive deleted.', 'info')
    return redirect(url_for('company_dashboard'))


@app.route('/company/drives/<int:drive_id>/applications')
@company_required
def company_drive_applications(drive_id):
    co     = current_user.company_profile
    drive  = PlacementDrive.query.filter_by(id=drive_id, company_id=co.id).first_or_404()
    status = request.args.get('status', '').strip()

    query = Application.query.filter_by(drive_id=drive_id).join(Student)
    if status:
        query = query.filter(Application.status == status)
    applications = query.order_by(Application.applied_at.desc()).all()

    return render_template('company_applications.html',
        drive=drive, applications=applications,
        status_filter=status, app_statuses=App_statuses)


@app.route('/company/applications/<int:app_id>/update', methods=['POST'])
@company_required
def company_update_application(app_id):
    co = current_user.company_profile
    application = Application.query.get_or_404(app_id)

    if application.drive.company_id != co.id:
        flash('Unauthorised.', 'danger')
        abort(403)

    new_status = request.form.get('status', Applied_status)
    if new_status not in App_statuses:
        flash('Invalid status.', 'warning')
        return redirect(url_for('company_drive_applications', drive_id=application.drive_id))

    application.status= new_status
    application.notes = request.form.get('notes', '').strip()
    db.session.commit()
    flash('Application status updated.', 'success')
    return redirect(url_for('company_drive_applications', drive_id=application.drive_id))


@app.route('/company/profile', methods=['GET', 'POST'])
@company_required
def company_profile():
    co = current_user.company_profile
    if request.method == 'POST':
        co.industry = request.form.get('industry', '').strip()
        co.location = request.form.get('location', '').strip()
        co.hr_name = request.form.get('hr_name', '').strip()
        co.hr_contact = request.form.get('hr_contact', '').strip()
        co.website = request.form.get('website', '').strip()
        co.description= request.form.get('description', '').strip()
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('company_profile'))
    return render_template('company_profile.html', company=co, industries=Industries)


        

@app.route('/student/dashboard')
@student_required
def student_dashboard():
    student = current_user.student_profile
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('index'))

    today = date.today()


    applied_drive_ids = [a.drive_id for a in student.applications]
    available_drives  = (PlacementDrive.query
                         .filter_by(status=Approved_status)
                         .filter(PlacementDrive.appication_deadline >= today)
                         .filter(PlacementDrive.id.notin_(applied_drive_ids) if applied_drive_ids else True)
                         .order_by(PlacementDrive.appication_deadline.asc())
                         .all())

    recent_apps= (Application.query.filter_by(student_id=student.id)
                      .order_by(Application.applied_at.desc()).limit(5).all())
    total_apps= Application.query.filter_by(student_id=student.id).count()
    applied_count= Application.query.filter_by(student_id=student.id, status=Applied_status).count()
    shortlisted_c = Application.query.filter_by(student_id=student.id, status=Shortlisted_status).count()
    selected_c = Application.query.filter_by(student_id=student.id, status=Selected_status).count()

    raw = (db.session.query(Application.status, func.count(Application.id))
           .filter(Application.student_id == student.id)
           .group_by(Application.status).all())
    my_data   = {s: c for s, c in raw}
    color_map = {Applied_status: BLUE, Shortlisted_status: AMBER,
                 Selected_status: GREEN, Rejected_app: RED}
    app_chart = chart(my_data, 'pie', 'My Applications',
                      colors=[color_map.get(k, GREY) for k in my_data])

    return render_template('student_dashboard.html',
        student=student,
        available_drives=available_drives,
        recent_apps=recent_apps,
        total_apps=total_apps,
        applied_count=applied_count,
        shortlisted_c=shortlisted_c,
        selected_c=selected_c,
        app_chart=app_chart)

    


@app.route('/student/drives')
@student_required
def student_drives():
    student = current_user.student_profile
    search  = request.args.get('search', '').strip()
    today   = date.today()

    query = (PlacementDrive.query.join(Company)
             .filter(PlacementDrive.status == Approved_status)
             .filter(PlacementDrive.appication_deadline >= today))
    if search:
        query = query.filter(or_(
            PlacementDrive.job_title.ilike(f'%{search}%'),
            Company.company_name.ilike(f'%{search}%'),
            PlacementDrive.req_skills.ilike(f'%{search}%'),
        ))
    drives = query.order_by(PlacementDrive.appication_deadline.asc()).all()

    applied_ids = {a.drive_id for a in student.applications}
    for d in drives:
        if d.appication_deadline:
            d.days_left = (d.appication_deadline - today).days
        else:
            d.days_left = 999

    return render_template('student_drives.html',
        drives=drives, search=search, applied_ids=applied_ids)


@app.route('/student/drives/<int:drive_id>/apply', methods=['POST'])
@student_required
def student_apply(drive_id):
    student = current_user.student_profile
    drive = PlacementDrive.query.get_or_404(drive_id)

    if not drive.is_open():
        flash("Sorry, This drive is not longer accepting applications.", "warning")
        return redirect(url_for('student_drives'))
    
    try:
        application = Application(student_id=student.id, drive_id=drive_id)
        db.session.add(application)
        db.session.commit()
        flash('Application submitted successfully..', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('You have already applied to this drive.', 'warning')

    return redirect(url_for('student_drives'))



@app.route('/student/applications')
@student_required
def student_applications():
    student = current_user.student_profile
    status  = request.args.get('status', '').strip()

    query = Application.query.filter_by(student_id=student.id)
    if status:
        query = query.filter_by(status=status)

    applications = query.order_by(Application.applied_at.desc()).all()

    return render_template('student_applications.html',
        applications=applications, status_filter=status, app_statuses = App_statuses)


@app.route('/student/history')
@student_required
def student_history():
    student = current_user.student_profile
    history = (Application.query
               .filter_by(student_id=student.id)
               .filter(Application.status.in_([Selected_status, Rejected_app]))
               .order_by(Application.applied_at.desc()).all())
    return render_template('student_history.html', history=history)


@app.route('/student/profile', methods=['GET', 'POST'])
@student_required
def student_profile():
    student = current_user.student_profile
    if request.method == 'POST':
        grad_yr  = request.form.get('grad_year', '').strip()
        cgpa_str = request.form.get('cgpa', '').strip()

        student.stu_name = request.form.get('stu_name', '').strip()
        student.phone = request.form.get('phone', '').strip()
        student.department = request.form.get('department', '').strip()
        student.degree = request.form.get('degree', '').strip()
        student.grad_year = int(grad_yr) if grad_yr.isdigit() else None
        student.cgpa = safe_float(cgpa_str)
        student.skills = request.form.get('skills', '').strip()
        student.bio = request.form.get('bio', '').strip()

        if 'resume' in request.files:
            f = request.files['resume']
            if f and f.filename and allowed_file(f.filename):
                resume_filename = secure_filename(
                    student.email.replace('@', '_').replace('.', '_') + '_resume.pdf'
                )
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], resume_filename))
                student.resume_filename = resume_filename

        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('student_profile'))

    return render_template('student_profile.html',
        student=student, departments = Departments, degrees=Degrees)


@app.errorhandler(403)
def forbidden(e):
    return render_template('error_403.html'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('error_404.html'), 404

@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return render_template('error_500.html'), 500


if __name__ == '__main__':
    init_db()
    app.run(debug=True)