from flask_sqlalchemy import SQLAlchemy
from flask import current_app
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import itsdangerous

db = SQLAlchemy()


# 📢 Notice Model
class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    file_type = db.Column(db.String(20), nullable=True)
    file_name = db.Column(db.String(150), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notice {self.title}>"

# 📅 Academic Calendar Upload Model
class CalendarUpload(db.Model):
    __tablename__ = "calendar_upload"

    id = db.Column(db.Integer, primary_key=True)
    session = db.Column(db.String(20), unique=True, nullable=False)
    filename = db.Column(db.String(150), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CalendarUpload session={self.session}>"
    























# ─────────────────────────────────────────────────────────────
# ✅ Association Table (Many-to-Many)
# ─────────────────────────────────────────────────────────────
student_course = db.Table('student_course',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id')),
    db.Column('course_id', db.Integer, db.ForeignKey('course.id'))
)

# ─────────────────────────────────────────────────────────────
# ✅ Student Model
# ─────────────────────────────────────────────────────────────
class Student(db.Model):
    __tablename__ = "student"

    id = db.Column(db.Integer, primary_key=True)
    roll = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    session = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    mobile = db.Column(db.String(20))
    father_name = db.Column(db.String(100))
    mother_name = db.Column(db.String(100))
    pass_year = db.Column(db.String(10))
    cgpa = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ Many-to-Many stitched relationship
    courses = db.relationship('Course', secondary=student_course, backref='students')

    def __repr__(self):
        return f"<Student {self.roll} - {self.name}>"

# ─────────────────────────────────────────────────────────────
# ✅ Session Model
# ─────────────────────────────────────────────────────────────
class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    start_year = db.Column(db.Integer, nullable=True)
    end_year = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Session {self.name}>"

# ─────────────────────────────────────────────────────────────
# ✅ Teacher Model
# ─────────────────────────────────────────────────────────────
class Teacher(db.Model):
    """👨‍🏫 Teacher model — stores login, profile, and course linkage"""
    __tablename__ = "teacher"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    mobile = db.Column(db.String(20))
    department = db.Column(db.String(100))
    joining_date = db.Column(db.Date)

    courses = db.relationship("Course", backref="teacher", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Teacher {self.name}>"

# ─────────────────────────────────────────────────────────────
# ✅ Course Model
# ─────────────────────────────────────────────────────────────
class Course(db.Model):
    """📚 Course model — linked to teacher, holds materials and attendance"""
    __tablename__ = "course"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey("teacher.id", name="fk_course_teacher_id"),
        nullable=True
    )

    session = db.Column(db.String(20), nullable=True)

    attendances = db.relationship("Attendance", backref="course", lazy=True)
    materials = db.relationship("CourseMaterial", backref="course", lazy=True)

    _table_args_ = (
        db.UniqueConstraint('code', 'session', name='unique_code_per_session'),
    )

    def __repr__(self):
        return f"<Course {self.code} - {self.name} ({self.session})>"

# ─────────────────────────────────────────────────────────────
# ✅ CourseMaterial Model
# ─────────────────────────────────────────────────────────────
class CourseMaterial(db.Model):
    __tablename__ = "course_material"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    session = db.Column(db.String(20), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("teacher.id"), nullable=False)

    def __repr__(self):
        return f"<Material {self.title} for Course {self.course_id}>"




# ─────────────────────────────────────────────────────────────
# ✅ Attendance Model
# ─────────────────────────────────────────────────────────────
class Attendance(db.Model):
    """📅 Attendance model — tracks student presence per course/date"""
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer,
        db.ForeignKey("student.id", name="fk_attendance_student_id"),
        nullable=False
    )
    course_id = db.Column(
        db.Integer,
        db.ForeignKey("course.id", name="fk_attendance_course_id"),
        nullable=False
    )
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)  # Present / Absent / Late

    def __repr__(self):
        return f"<Attendance Student:{self.student_id} Course:{self.course_id} Date:{self.date} status:{self.status}>"