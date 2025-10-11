from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, send_file
from models import Teacher, Course, CourseMaterial, db, Attendance, Student, Session
from sqlalchemy.orm import joinedload
from datetime import datetime

import os
from werkzeug.utils import secure_filename
teacher_routes = Blueprint("teacher_routes", __name__)
teacher_routes = Blueprint("teacher_routes", __name__, url_prefix="/teacher")

# 🔧 Utility: Generate stitched session list
def generate_sessions(start_year=2009, count=100):
    return [f"{y}-{y+1}" for y in range(start_year, start_year + count)]


# ─────────────────────────────────────────────────────────────
# ✅ Teacher Login
# ─────────────────────────────────────────────────────────────
@teacher_routes.route("/login", methods=["GET", "POST"], endpoint="teacher_login")
def teacher_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        teacher = Teacher.query.filter_by(email=email).first()
        if not teacher or not teacher.check_password(password):
            flash("❌ Invalid email or password.", "danger")
            return redirect(url_for("teacher_routes.teacher_login"))

        session["teacher_id"] = teacher.id
        flash("✅ Login successful.", "success")
        return redirect(url_for("teacher_routes.teacher_panel"))

    return render_template("teacher/login.html")




##############################################################################################33
# ─────────────────────────────────────────────
# ✅ Course Creation Form
# ─────────────────────────────────────────────
@teacher_routes.route("/course/add-form", methods=["GET"], endpoint="course_add_form")
def course_add_form():
    teacher_id = session.get("teacher_id")
    if not teacher_id:
        flash("⚠️ Unauthorized access. Please log in as a teacher.", "danger")
        return redirect(url_for("public_routes.teacher_login"))

    session_list = generate_sessions()
    return render_template("teacher/add_course.html", teacher_id=teacher_id, session_list=session_list)

@teacher_routes.route("/course/add", methods=["POST"], endpoint="course_add")
def course_add():
    teacher_id = session.get("teacher_id")
    if not teacher_id:
        flash("⚠️ Unauthorized access. Please log in as a teacher.", "danger")
        return redirect(url_for("public_routes.teacher_login"))

    title = request.form.get("title")
    code = request.form.get("code")
    session_name = request.form.get("session")

    if not title or not code or not session_name:
        flash("⚠️ All fields are required!", "danger")
        return redirect(url_for("teacher_routes.course_add_form"))

    new_course = Course(
        name=title.strip(),
        code=code.strip(),
        session=session_name.strip(),
        teacher_id=teacher_id
    )
    db.session.add(new_course)
    db.session.commit()

    flash("✅ Course added successfully!", "success")
    return redirect(url_for("teacher_routes.upload_material", course_id=new_course.id))


@teacher_routes.route("/my-courses", methods=["GET"], endpoint="my_courses")
def my_courses():
    teacher_id = session.get("teacher_id")
    session_list = generate_sessions()
    selected_session = request.args.get("session")

    courses = []
    if selected_session:
        courses = Course.query.filter_by(
            teacher_id=teacher_id,
            session=selected_session
        ).all()

    return render_template(
        "teacher/my_courses.html",
        courses=courses,
        session_list=session_list,
        selected_session=selected_session,
        teacher_id=teacher_id
    )

# ─────────────────────────────────────────────
# ✅ Upload Material
# ─────────────────────────────────────────────
@teacher_routes.route("/upload-material", methods=["GET", "POST"], endpoint="upload_material")
def upload_material():
    teacher_id = session.get("teacher_id")
    session_list = generate_sessions()
    selected_session = request.args.get("session")

    if not selected_session and session_list:
        selected_session = session_list[0]

    if request.method == "POST":
        file = request.files.get("file")
        title = request.form.get("title")
        course_id = request.form.get("course_id")

        if file and title and course_id and selected_session:
            filename = secure_filename(file.filename)
            UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            material = CourseMaterial(
                title=title.strip(),
                filename=filename,
                course_id=int(course_id),
                session=selected_session.strip(),
                upload_time=datetime.utcnow(),
                uploaded_by=teacher_id
            )
            db.session.add(material)
            db.session.commit()

            flash("✅ File uploaded successfully!", "success")
            return redirect(url_for("teacher_routes.view_materials", course_id=course_id, session=selected_session))
        else:
            flash("⚠️ All fields are required!", "danger")
            return redirect(url_for("teacher_routes.upload_material", session=selected_session))

    courses = []
    if selected_session:
        courses = Course.query.filter_by(
            teacher_id=teacher_id,
            session=selected_session
        ).all()

    return render_template(
        "teacher/upload_material.html",
        courses=courses,
        session_list=session_list,
        selected_session=selected_session
    )

# ─────────────────────────────────────────────
# ✅ View Materials
# ─────────────────────────────────────────────
@teacher_routes.route("/course/<int:course_id>/materials", methods=["GET"])
def view_materials(course_id):
    teacher_id = session.get("teacher_id")
    if not teacher_id:
        flash("⚠️ Unauthorized access. Please log in as a teacher.", "danger")
        return redirect(url_for("public_routes.teacher_login"))

    selected_session = request.args.get("session")

    course = Course.query.filter_by(id=course_id, teacher_id=teacher_id).first()
    if not course:
        flash("⚠️ Course not found or access denied.", "danger")
        return redirect(url_for("teacher_routes.my_courses"))

    session_list = db.session.query(CourseMaterial.session).filter_by(course_id=course_id).distinct().all()
    session_list = [s[0] for s in session_list if s[0]]

    if not selected_session and session_list:
        selected_session = session_list[0]

    materials = CourseMaterial.query.filter_by(
        course_id=course_id,
        session=selected_session,
        uploaded_by=teacher_id
    ).order_by(CourseMaterial.upload_time.desc()).all()

    return render_template("teacher/view_materials.html",
                           course=course,
                           materials=materials,
                           session_list=session_list,
                           selected_session=selected_session)

# ─────────────────────────────────────────────
# ✅ Session Generator
# ─────────────────────────────────────────────
def generate_sessions():
    sessions = db.session.query(Course.session).distinct().filter(Course.session != "").order_by(Course.session.desc()).all()
    return [s[0] for s in sessions]


# 📥 Direct Upload to Course
@teacher_routes.route("/teacher/<int:course_id>/material/upload", methods=["POST"], endpoint="material_upload")
def material_upload(course_id):
    title = request.form.get("title")
    file = request.files.get("file")

    if not file or not title:
        flash("⚠️ Title and file are required.", "danger")
        return redirect(url_for("teacher_routes.material_upload_form", course_id=course_id))

    filename = secure_filename(file.filename)
    file.save(os.path.join(os.getcwd(), "uploads", filename))

    new_material = CourseMaterial(
        course_id=course_id,
        title=title.strip(),
        filename=filename,
        upload_time=datetime.utcnow()
    )
    db.session.add(new_material)
    db.session.commit()

    flash("✅ Material uploaded successfully.", "success")
    return redirect(url_for("teacher_routes.view_materials", course_id=course_id))














#############################################################
@teacher_routes.route("/attendance-dashboard")
def attendance_dashboard():
    teacher_id = session.get("teacher_id")
    if not teacher_id:
        flash("🔐 Please login first", "danger")
        return redirect(url_for("public_routes.teacher_login"))

    courses = Course.query.filter_by(teacher_id=teacher_id).all()
    return render_template("teacher/attendance_dashboard.html", courses=courses)

@teacher_routes.route("/attendance-summary/<int:course_id>")
def attendance_summary(course_id):
    course = Course.query.get_or_404(course_id)
    records = Attendance.query.filter_by(course_id=course_id).order_by(Attendance.date.desc()).all()
    return render_template("teacher/attendance_summary.html", course=course, records=records)

@teacher_routes.route("/attendance-export/<int:course_id>")
def attendance_export(course_id):
    course = Course.query.get_or_404(course_id)
    records = Attendance.query.filter_by(course_id=course_id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student Roll", "Name", "Date", "Status"])
    for r in records:
        student = Student.query.get(r.student_id)
        writer.writerow([student.roll, student.name, r.date, r.status])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=attendance_{course.code}.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@teacher_routes.route("/attendance-delete/<int:course_id>", methods=["POST"])
def attendance_delete(course_id):
    course = Course.query.get_or_404(course_id)
    Attendance.query.filter_by(course_id=course_id).delete()
    db.session.commit()
    flash("🗑️ Attendance records deleted", "warning")
    return redirect(url_for("teacher_routes.attendance_dashboard"))


@teacher_routes.route("/attendance/<int:course_id>", methods=["GET", "POST"])
def attendance_panel(course_id):
    course = Course.query.get_or_404(course_id)
    session_name = course.session  # ✅ stitched from course.session string

    # ✅ stitched student filter: enrolled in course AND matching session
    students = [
        student for student in course.students
        if student.session == session_name
    ]

    if request.method == "POST":
        date = request.form.get("date")
        for student in students:
            status = request.form.get(f"status_{student.id}")
            if status:
                existing = Attendance.query.filter_by(
                    student_id=student.id,
                    course_id=course.id,
                    date=date
                ).first()
                if not existing:
                    entry = Attendance(
                        student_id=student.id,
                        course_id=course.id,
                        date=date,
                        status=status,
                        session=session_name  # ✅ stitched session save
                    )
                    db.session.add(entry)
        db.session.commit()
        flash("✅ Attendance saved successfully", "success")
        return redirect(url_for('teacher_routes.attendance_panel', course_id=course.id))

    return render_template(
        "teacher/attendance_panel.html",
        course=course,
        students=students,
        session_name=session_name
    )

@teacher_routes.route("/attendance-selector", methods=["GET", "POST"])
def attendance_selector():
    teacher_id = session.get("teacher_id")
    courses = Course.query.filter_by(teacher_id=teacher_id).all()
    sessions = Session.query.all()  # ✅ Always available

    if request.method == "POST":
        course_id = request.form.get("course_id")
        session_name = request.form.get("session_name")
        return redirect(url_for("teacher_routes.attendance_panel", course_id=course_id, session_name=session_name))

    # ✅ Always render template with sessions
    return render_template("teacher/attendance_selector.html", courses=courses, sessions=sessions)