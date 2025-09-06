from extensions import db

# ─────────────────────────────────────────────
# ✅ Student Model
# ─────────────────────────────────────────────
class Student(db.Model):
    __tablename__ = "student"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll = db.Column(db.String(50), unique=True, nullable=False)
    reg = db.Column(db.String(50), nullable=True)
    mobile = db.Column(db.String(20))
    email = db.Column(db.String(100))
    department = db.Column(db.String(50))
    father_name = db.Column(db.String(100), nullable= True)
    mother_name = db.Column(db.String(100))
    cgpa = db.Column(db.String(10))
    pass_year = db.Column(db.String(10))

    session_id = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=False)
    session = db.relationship("Session", back_populates="students")  # ✅ fixed here
    is_active = db.Column(db.Boolean, default=True)
    testimonial = db.Column(db.Text, nullable=True)

    attendances = db.relationship("Attendance", backref="student", lazy=True)

    def __repr__(self):
        return f"<Student {self.roll} - {self.name}>"
    

# ─────────────────────────────────────────────
# ✅ Session Model
# ─────────────────────────────────────────────
class Session(db.Model):
    __tablename__ = "session"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)

    students = db.relationship("Student", back_populates="session", lazy=True)
    
    
    
# ─────────────────────────────────────────────────────────────
# ✅ Teacher Model
# ─────────────────────────────────────────────────────────────
class Teacher(db.Model):
    __tablename__ = "teacher"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    designation = db.Column(db.String(100))

    courses = db.relationship("Course", backref="teacher", lazy=True)

    def __repr__(self):
        return f"<Teacher {self.name}>"

# ─────────────────────────────────────────────────────────────
# ✅ Course Model
# ─────────────────────────────────────────────────────────────
class Course(db.Model):
    __tablename__ = "course"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False, unique=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teacher.id"), nullable=False)

    attendances = db.relationship("Attendance", backref="course", lazy=True)


    def __repr__(self):
        return f"<Course {self.code} - {self.name}>"

# ─────────────────────────────────────────────────────────────
# ✅ Attendance Model
# ─────────────────────────────────────────────────────────────
class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)  # Present / Absent / Late

    def __repr__(self):
        return f"<Attendance Student:{self.student_id} Course:{self.course_id} Date:{self.date} status:{self.status}>"
    


class CourseMaterial(db.Model):
    __tablename__ = 'course_material'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    filetype = db.Column(db.String(20), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

    course = db.relationship('Course', backref=db.backref('materials', lazy=True))

    def __repr__(self):
        return f"<Material {self.title} ({self.filetype}) for Course:{self.course_id}>"