from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

from datetime import datetime

db = SQLAlchemy()

Admin_role = 'admin'
Company_role = 'company'
Student_role = 'student'

Pending_status = "pending"
Approved_status = "approved"
Rejected_status = "rejected"
Closed_status = "closed"

Applied_status = "Applied"
Shortlisted_status = "Shortlisted"
Selected_status = "Selected"
Rejected_status = "Rejected"

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(191), unique=True, nullable=False, index=True)
    passwd = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default= datetime.utcnow)
    updated_at = db.Column(db.DateTime, default= datetime.utcnow, onupdate=datetime.utcnow)
    is_blacklisted = db.Column(db.Boolean, default=False)
    def is_admin(self):
        return self.role == Admin_role
    def is_company(self):
        return self.role == Company_role
    def is_student(self):
        return self.role == Student_role

class Company(db.Model):
    __tablename__ = "companies"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    company_name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(100))
    hr_name = db.Column(db.String(100))
    hr_contact = db.Column(db.String(100))
    website = db.Column(db.String(200))
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    approval_status = db.Column(db.String(30), default='pending', nullable=False)
    registered_at = db.Column(db.DateTime, default= datetime.utcnow)
    updated_at = db.Column(db.DateTime, default= datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_approved(self):
        return self.approval_status == Approved_status


class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    stu_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(191), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    roll_no = db.Column(db.String(50), unique=True)
    department = db.Column(db.String(100))
    degree = db.Column(db.String(60))
    grad_year = db.Column(db.Integer)
    cgpa = db.Column(db.Float)
    skilss = db.Column(db.Text)
    resume_filename = db.Column(db.String(200))
    registered_at = db.Column(db.DateTime, default= datetime.utcnow)
    updated_at = db.Column(db.DateTime, default= datetime.utcnow, onupdate=datetime.utcnow)

class PlacementDrive(db.Model):
    __tablename__ = "placement_drives"
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    job_title = db.Column(db.String(200), nullable=False)
    job_desp = db.Column(db.Text)
    job_type = db.Column(db.String(50))
    eligible_criteria = db.Column(db.Text)
    req_skills = db.Column(db.Text)
    salary_range = db.Column(db.String(100))
    location = db.Column(db.String(100))
    appication_deadline = db.Column(db.Date)
    status = db.Column(db.String(30), default='peniding', nullable=False)
    created_at = db.Column(db.DateTime, default= datetime.utcnow)
    updated_at = db.Column(db.DateTime, default= datetime.utcnow, onupdate=datetime.utcnow)

    def is_active(self):
        return (self.status == Approved_status and 
                self.appication_deadline and 
                self.appication_deadline >= datetime.date.today()
                )


class Application(db.Model):
    __tablename__ = "applications"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drives.id'), nullable=False)
    status = db.Column(db.String(30), default='pending', nullable=False)
    applied_at = db.Column(db.DateTime, default= datetime.utcnow)
    notes = db.Column(db.Text)
    

    

    