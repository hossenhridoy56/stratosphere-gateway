# 🔹 Flask Core
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, send_file, jsonify, session
)

# 🔹 File Handling & Security
import os
from werkzeug.utils import secure_filename

# 🔹 Database & Models
from extensions import db
from models import (
    Student, Teacher, Course, Attendance,
    Session, CourseMaterial
)

# 🔹 Utilities
from datetime import datetime
from io import BytesIO
import pandas as pd
from xhtml2pdf import pisa  # PDF generation
import requests  # ✅ For external API calls (e.g., weather forecast)
from urllib.parse import quote  # ✅ For safe location encoding

# 🔹 Upload Folder Setup
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

api_routes = Blueprint("api", __name__)

# ─────────────────────────────────────────────────────────────
# ✅ Homepage
# ─────────────────────────────────────────────────────────────
@api_routes.route("/", endpoint="home")
def home():
    return render_template("home.html")



# 🔹 Add Student (Manual + Excel)
@api_routes.route("/student/add", methods=["GET", "POST"], endpoint="add_student")
@login_required
def add_student():
    sessions = [f"{2009+i}-{2010+i}" for i in range(100)]

    if request.method == "POST":
        if "student_file" in request.files:
            # 🔹 Excel Upload
            file = request.files.get("student_file")
            session_name = request.form.get("upload_session")
            if not file or not session_name:
                flash("⚠️ Missing file or session", "danger")
                return redirect(url_for("api.add_student"))

            session_obj = Session.query.filter_by(name=session_name).first()
            if not session_obj:
                flash(f"⚠️ Session '{session_name}' not found!", "danger")
                return redirect(url_for("api.add_student"))

            try:
                df = pd.read_csv(file) if file.filename.endswith(".csv") else pd.read_excel(file)
            except Exception as e:
                flash(f"⚠️ File read error: {str(e)}", "danger")
                return redirect(url_for("api.add_student"))

            for _, row in df.iterrows():
                if not row.get("name") or not row.get("roll"):
                    continue
                exists = Student.query.filter_by(roll=row.get("roll"), session_id=session_obj.id).first()
                if exists:
                    continue
                student = Student(
                    name=row.get("name"),
                    roll=row.get("roll"),
                    reg=row.get("reg"),
                    mobile=row.get("mobile"),
                    email=row.get("email"),
                    department=row.get("department"),
                    father_name=row.get("father_name"),
                    mother_name=row.get("mother_name"),
                    cgpa=row.get("cgpa"),
                    pass_year=row.get("pass_year"),
                    session=session_obj,
                    testimonial=row.get("testimonial"),
                    is_active=True
                )
                db.session.add(student)
            db.session.commit()
            flash("✅ Students uploaded successfully!", "success")
            return redirect(url_for("api.add_student"))

        else:
            # 🔹 Manual Entry
            name = request.form.get("name")
            roll = request.form.get("roll")
            session_name = request.form.get("session")
            if not name or not roll or not session_name:
                flash("⚠️ Name, Roll, and Session are required!", "danger")
                return redirect(url_for("api.add_student"))

            session_obj = Session.query.filter_by(name=session_name).first()
            if not session_obj:
                flash(f"⚠️ Session '{session_name}' not found!", "danger")
                return redirect(url_for("api.add_student"))

            exists = Student.query.filter_by(roll=roll, session_id=session_obj.id).first()
            if exists:
                flash(f"⚠️ Roll '{roll}' already exists!", "danger")
                return redirect(url_for("api.add_student"))

            student = Student(
                name=name,
                roll=roll,
                reg=request.form.get("reg"),
                mobile=request.form.get("mobile"),
                email=request.form.get("email"),
                department=request.form.get("department"),
                father_name=request.form.get("father_name"),
                mother_name=request.form.get("mother_name"),
                cgpa=request.form.get("cgpa"),
                pass_year=request.form.get("pass_year"),
                session=session_obj,
                testimonial=request.form.get("testimonial"),
                is_active=True
            )
            db.session.add(student)
            db.session.commit()
            flash("✅ Student added successfully!", "success")
            return redirect(url_for("api.add_student"))

    return render_template("add_student.html", sessions=sessions)

# 🔹 Session Dashboard
@api_routes.route("/students/session", methods=["GET", "POST"], endpoint="session_dashboard")
@login_required
def session_dashboard():
    selected_session = request.form.get("session") if request.method == "POST" else request.args.get("session")
    sessions = [f"{2009+i}-{2010+i}" for i in range(100)]
    students = []

    if selected_session:
        session_obj = Session.query.filter_by(name=selected_session).first()
        if session_obj:
            students = Student.query.filter_by(session_id=session_obj.id).order_by(Student.roll.asc()).all()

    return render_template("student_info.html", sessions=sessions, students=students, selected_session=selected_session)

# 🔹 Edit Student
@api_routes.route("/student/edit/<int:id>", methods=["GET", "POST"], endpoint="edit_student")
@login_required
def edit_student(id):
    if current_user.role not in ["admin", "teacher"]:
        flash("❌ Unauthorized access", "danger")
        return redirect(url_for("api.session_dashboard"))

    student = Student.query.get_or_404(id)

    if request.method == "POST":
        roll = request.form.get("roll")
        if not roll:
            flash("⚠️ Roll is required!", "danger")
            return redirect(request.referrer)

        student.roll = roll.strip()
        student.name = request.form.get("name")
        student.reg = request.form.get("reg")
        student.mobile = request.form.get("mobile")
        student.email = request.form.get("email")
        student.department = request.form.get("department")
        student.father_name = request.form.get("father_name")
        student.mother_name = request.form.get("mother_name")
        student.cgpa = request.form.get("cgpa")
        student.pass_year = request.form.get("pass_year")
        student.testimonial = request.form.get("testimonial")

        try:
            db.session.commit()
            flash("✅ Student updated successfully!", "success")
            return redirect(url_for("api.session_dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Update failed: {str(e)}", "danger")
            return redirect(request.referrer)

    return render_template("edit_student.html", student=student)

# 🔹 Delete Student
@api_routes.route("/student/delete/<int:id>", methods=["POST"], endpoint="delete_student")
@login_required
def delete_student(id):
    if current_user.role not in ["admin", "teacher"]:
        flash("❌ Unauthorized access", "danger")
        return redirect(url_for("api.session_dashboard"))

    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash("✅ Student deleted successfully!", "success")
    return redirect(url_for("api.session_dashboard"))

# 🔹 Export Students
@api_routes.route("/students/export", methods=["GET", "POST"], endpoint="export_students")
@login_required
def export_students():
    session_name = request.form.get("session") if request.method == "POST" else request.args.get("session")
    format = request.form.get("format", "excel") if request.method == "POST" else request.args.get("format", "excel")

    if not session_name:
        flash("⚠️ Please select a session to export!", "danger")
        return redirect(url_for("api.session_dashboard"))

    session_obj = Session.query.filter_by(name=session_name).first()
    if not session_obj:
        flash(f"⚠️ Session '{session_name}' not found!", "danger")
        return redirect(url_for("api.session_dashboard"))

    students = Student.query.filter_by(session_id=session_obj.id).order_by(Student.roll.asc()).all()
    if not students:
        flash("⚠️ No students found for this session!", "warning")
        return redirect(url_for("api.session_dashboard"))

    data = [{
        "Roll": s.roll,
        "Name": s.name,
        "Mobile": s.mobile or "",
        "Email": s.email or "",
        "Father's Name": s.father_name or "",
        "Mother's Name": s.mother_name or "",
        "Passing Year": s.pass_year or "",
        "CGPA": s.cgpa or ""
    } for s in students]

    df = pd.DataFrame(data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    if format.lower() == "pdf":
        html = f"<meta charset='UTF-8'>{df.to_html(index=False)}"
        pdf = BytesIO()
        pisa.CreatePDF(html, dest=pdf)
        pdf.seek(0)
        return send_file(
            pdf,
            download_name=f"students_{session_name}_{timestamp}.pdf",
            as_attachment=True,
            mimetype="application/pdf"
        )
    else:
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Students")
            workbook = writer.book
            worksheet = writer.sheets["Students"]

            # Optional formatting
            format_header = workbook.add_format({'bold': True, 'bg_color': '#DDEEFF'})
            worksheet.set_row(0, None, format_header)
            worksheet.set_column(0, len(df.columns)-1, 20)

        output.seek(0)
        return send_file(
            output,
            download_name=f"students_{session_name}_{timestamp}.xlsx",
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
# ─────────────────────────────────────────────────────────────
# ✅ Teacher Panel
# ─────────────────────────────────────────────────────────────
@api_routes.route("/teachers", methods=["GET", "POST"], endpoint="teacher_panel")
def teacher_panel_view():
    if request.method == "POST":
        name = request.form.get("name")
        designation = request.form.get("designation")
        if name:
            teacher = Teacher(name=name.strip(), designation=designation.strip() if designation else None)
            db.session.add(teacher)
            db.session.commit()
            flash("✅ Teacher added successfully!", "success")

    teachers = Teacher.query.order_by(Teacher.name.asc()).all()
    return render_template("teacher_panel.html", teachers=teachers)

# ─────────────────────────────────────────────────────────────
# ✅ Edit/Delete Teacher
# ─────────────────────────────────────────────────────────────
@api_routes.route("/teacher/<int:teacher_id>/edit", methods=["GET", "POST"], endpoint="edit_teacher")
def edit_teacher_view(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    if request.method == "POST":
        teacher.name = request.form.get("name")
        teacher.designation = request.form.get("designation")
        db.session.commit()
        flash("✅ Teacher updated!", "success")
        return redirect(url_for("api.teacher_panel"))
    return render_template("edit_teacher.html", teacher=teacher)

@api_routes.route("/teacher/<int:teacher_id>/delete", methods=["POST"], endpoint="delete_teacher")
def delete_teacher_view(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    db.session.delete(teacher)
    db.session.commit()
    flash("❌ Teacher deleted!", "success")
    return redirect(url_for("api.teacher_panel"))

# ─────────────────────────────────────────────────────────────
# ✅ Teacher Dashboard + Course Add/Delete + Session List
# ─────────────────────────────────────────────────────────────
@api_routes.route("/teacher/<int:teacher_id>/dashboard", endpoint="teacher_dashboard_by_id")
def teacher_dashboard_view(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    courses = Course.query.filter_by(teacher_id=teacher_id).all()

    course_data = []
    for course in courses:
        student_count = Attendance.query.filter_by(course_id=course.id).distinct(Attendance.student_id).count()
        course_data.append({
            "id": course.id,
            "title": course.name,
            "code": course.code,
            "student_count": student_count
        })

    # ✅ FIXED: Get distinct sessions via join and sort by Session.name
    active_sessions = (
        db.session.query(Session)
        .join(Student)
        .filter(Student.is_active.is_(True))
        .distinct()
        .order_by(Session.name.asc())
        .all()
    )
    session_list = [s.name for s in active_sessions]

    return render_template("teacher_dashboard.html", teacher=teacher, courses=course_data, session_list=session_list)



@api_routes.route("/teacher/<int:teacher_id>/course/add", methods=["POST"], endpoint="course_add")
def course_add_view(teacher_id):
    title = request.form.get("title")
    code = request.form.get("code")

    if not title or not code:
        flash("⚠️ Title and Code are required!", "danger")
        return redirect(url_for("api.teacher_dashboard_by_id", teacher_id=teacher_id))

    # ✅ Check if course code already exists
    existing = Course.query.filter_by(code=code).first()
    if existing:
        flash(f"⚠️ Course code '{code}' already exists!", "danger")
        return redirect(url_for("api.teacher_dashboard_by_id", teacher_id=teacher_id))

    # ✅ Safe to add
    course = Course(name=title.strip(), code=code.strip(), teacher_id=teacher_id)
    db.session.add(course)
    db.session.commit()
    flash("✅ Course added successfully!", "success")
    return redirect(url_for("api.teacher_dashboard_by_id", teacher_id=teacher_id))

@api_routes.route("/course/<int:course_id>/delete", methods=["POST"], endpoint="course_delete_by_id")
def course_delete_view(course_id):
    course = Course.query.get_or_404(course_id)
    teacher_id = course.teacher_id
    db.session.delete(course)
    db.session.commit()
    flash("❌ Course deleted!", "success")
    return redirect(url_for("api.teacher_dashboard_by_id", teacher_id=teacher_id))

# ─────────────────────────────────────────────
# ✅ Attendance Entry Page
# ─────────────────────────────────────────────
@api_routes.route("/course/<int:course_id>/attendance", methods=["GET"], endpoint="course_attendance")
def course_attendance_view(course_id):
    session_name = request.args.get("session")
    course = Course.query.get_or_404(course_id)

    # ✅ Only sessions with students
    sessions = (
        db.session.query(Session)
        .join(Student)
        .filter(Student.is_active.is_(True))
        .distinct()
        .order_by(Session.name.asc())
        .all()
    )

    if session_name:
        students = Student.query.filter(
            Student.session.has(name=session_name),
            Student.is_active.is_(True)
        ).order_by(Student.roll.asc()).all()
    else:
        students = Student.query.filter_by(is_active=True).order_by(Student.roll.asc()).all()

    return render_template(
        "course_attendance.html",
        course=course,
        students=students,
        session=session_name,
        sessions=sessions  # ✅ stitched dropdown
    )

# ─────────────────────────────────────────────
# ✅ Save Attendance → Redirect to Summary
# ─────────────────────────────────────────────
@api_routes.route("/course/<int:course_id>/attendance/save", methods=["POST"], endpoint="course_attendance_save")
def course_attendance_save(course_id):
    date_str = request.form.get("date")  # ✅ Step 2: Get date as string
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()  # ✅ Step 2: Convert to Python date
    except ValueError:
        flash("⚠️ Invalid date format", "danger")
        return redirect(request.referrer)

    saved = 0
    for key in request.form:
        if key.startswith("status_"):
            roll = key.replace("status_", "")
            status = request.form.get(key)

            student = Student.query.filter_by(roll=roll).first()
            if student:
                att = Attendance(
                    student_id=student.id,
                    course_id=course_id,
                    date=date_obj,  # ✅ Step 3: Use converted date
                    status=status
                )
                db.session.add(att)
                saved += 1

    try:
        db.session.commit()
        flash(f"✅ Attendance saved for {saved} students", "success")
        return redirect(url_for("api.attendance_summary", course_id=course_id))  # ✅ Redirect to summary
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Save failed: {str(e)}", "danger")
        return redirect(request.referrer)

# ─────────────────────────────────────────────
# ✅ Attendance Summary View
# ─────────────────────────────────────────────
@api_routes.route("/course/<int:course_id>/attendance/summary", endpoint="attendance_summary")
def attendance_summary_view(course_id):
    course = Course.query.get_or_404(course_id)
    students = Student.query.join(Attendance).filter(
        Attendance.course_id == course_id
    ).distinct().all()

    summary = []
    for student in students:
        total = Attendance.query.filter_by(student_id=student.id, course_id=course_id).count()
        present = Attendance.query.filter_by(student_id=student.id, course_id=course_id, status="Present").count()
        absent = total - present
        summary.append({
            "name": student.name,
            "roll": student.roll,
            "present": present,
            "absent": absent,
            "total": total
        })

    return render_template("attendance_summary.html", course=course, summary=summary)

# ─────────────────────────────────────────────────────────────
# ✅ Course Materials
# ─────────────────────────────────────────────────────────────
# ✅ Course Material Upload (Teacher)
@api_routes.route("/course/upload", methods=["GET", "POST"], endpoint="upload_material")
def upload_material():
    if request.method == "POST":
        file = request.files.get("file")
        title = request.form.get("title")
        course_id = request.form.get("course_id")

        if file and title and course_id:
            # ✅ Safe filename
            filename = secure_filename(file.filename)

            # ✅ Ensure uploads folder exists
            UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            # ✅ Save file
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            # ✅ Safe filetype fallback
            filetype = file.content_type or "application/octet-stream"

            # ✅ Create material entry
            material = CourseMaterial(
                title=title,
                filename=filename,
                filetype=filetype,
                course_id=int(course_id)
            )
            db.session.add(material)
            db.session.commit()

            flash("✅ File uploaded successfully!", "success")
            return redirect(url_for("api.upload_material"))

    # ✅ Load all courses for dropdown + preview
    courses = Course.query.all()
    return render_template("upload_material.html", courses=courses)

# ✅ Course Material View (Student)
@api_routes.route("/course/<int:course_id>/materials", methods=["GET"], endpoint="view_materials")
def view_materials(course_id):
    course = Course.query.get_or_404(course_id)
    materials = CourseMaterial.query.filter_by(course_id=course_id).all()
    return render_template("view_materials.html", course=course, materials=materials)


@api_routes.route("/material/<int:id>/download", methods=["GET"], endpoint="download_material")
def download_material(id):
    material = CourseMaterial.query.get_or_404(id)
    filepath = os.path.join(os.getcwd(), "uploads", material.filename)

    if not os.path.exists(filepath):
        flash("❌ File not found on server", "danger")
        return redirect(url_for("api.view_materials", course_id=material.course_id))

    try:
        return send_file(
            filepath,
            mimetype=material.filetype or "application/octet-stream",
            as_attachment=True
        )
    except Exception as e:
        flash(f"❌ Could not download: {str(e)}", "danger")
        return redirect(url_for("api.view_materials", course_id=material.course_id))


@api_routes.route("/material/<int:id>/delete", methods=["POST"], endpoint="delete_material")
def delete_material(id):
    material = CourseMaterial.query.get_or_404(id)
    filepath = os.path.join(os.getcwd(), "uploads", material.filename)

    # ✅ Delete file from disk
    if os.path.exists(filepath):
        os.remove(filepath)

    # ✅ Delete from DB
    db.session.delete(material)
    db.session.commit()
    flash("🗑️ Material deleted successfully!", "success")
    return redirect(url_for("api.upload_material"))


# ─────────────────────────────────────────────
# ✅ Testimonial Preview View
# ─────────────────────────────────────────────
@api_routes.route("/testimonial/view/<string:roll>", endpoint="testimonial_view_page")
def testimonial_view_page(roll):
    student = Student.query.filter_by(roll=roll).first_or_404()
    context = {
        "student_name": student.name,
        "father_name": student.father_name,
        "mother_name": student.mother_name,
        "session_name": student.session.name,  # stitched from relationship
        "passing_year": student.pass_year,
        "cgpa": student.cgpa,
        "date": datetime.today().strftime("%d %B %Y"),
        "roll": student.roll
    }
    return render_template("testimonial_view.html", **context)

# ─────────────────────────────────────────────
# ✅ Testimonial PDF Download
# ─────────────────────────────────────────────
@api_routes.route("/testimonial/<string:roll>/download", endpoint="download_testimonial_pdf_v2")
def download_testimonial_pdf_v2(roll):
    student = Student.query.filter_by(roll=roll).first_or_404()
    date = datetime.today().strftime("%d %B %Y")
    logo_path = url_for('static', filename='images/logo.png')

    html = render_template("testimonial_pdf.html",
        student_name=student.name,
        father_name=student.father_name,
        mother_name=student.mother_name,
        session_name=student.session.name,
        passing_year=student.pass_year,
        cgpa=student.cgpa,
        roll=student.roll,
        date=date,
        logo_path=logo_path
    )

    pdf = BytesIO()
    pisa.CreatePDF(html, dest=pdf)
    pdf.seek(0)
    return send_file(pdf, download_name=f"testimonial_{student.roll}.pdf", as_attachment=True)
# ─────────────────────────────────────────────
# ✅ Testimonial Archive
# ─────────────────────────────────────────────
@api_routes.route("/testimonial/archive", methods=["GET", "POST"], endpoint="testimonial_archive")
def testimonial_archive_view():
    selected_session = request.form.get("session")
    sessions = db.session.query(Student.session).distinct().order_by(Student.session.asc()).all()

    students = Student.query.filter_by(session=selected_session).filter(Student.pass_year.isnot(None)).order_by(Student.roll.asc()).all() if selected_session else []

    return render_template("testimonial_archive.html",
        students=students,
        sessions=[s[0] for s in sessions],
        selected_session=selected_session,
        date=datetime.today().strftime("%Y")
    )


# ─────────────────────────────────────────────
# ✅ Document Generator
# ─────────────────────────────────────────────
@api_routes.route("/generate", methods=["GET", "POST"], endpoint="generate")
def generate_document_view():
    if request.method == "POST":
        name = request.form.get("name")
        role = request.form.get("role")
        roll = request.form.get("roll")
        registration = request.form.get("registration")
        session = request.form.get("session")
        recipient = request.form.get("recipient")
        subject = request.form.get("subject")
        request_type = request.form.get("request_type", "").lower()
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        return render_template(
            "document_preview.html",
            name=name,
            role=role,
            roll=roll,
            registration=registration,
            session=session,
            recipient=recipient,
            subject=subject,
            request_type=request_type,
            start_date=start_date,
            end_date=end_date,
            now=datetime.now()
        )

    return render_template("document_form.html")


@api_routes.route("/document/pdf", methods=["POST"], endpoint="generate_document_pdf")
def generate_document_pdf():
    html = render_template(
        "document_pdf.html",
        name=request.form.get("name"),
        role=request.form.get("role"),
        roll=request.form.get("roll"),
        registration=request.form.get("registration"),
        session=request.form.get("session"),
        recipient=request.form.get("recipient"),
        subject=request.form.get("subject"),
        request_type=request.form.get("request_type", "").lower(),
        start_date=request.form.get("start_date"),
        end_date=request.form.get("end_date"),
        now=datetime.now()
    )
    pdf = BytesIO()
    pisa.CreatePDF(html, dest=pdf)
    pdf.seek(0)
    return send_file(pdf, download_name="generated_document.pdf", as_attachment=True)

# ─────────────────────────────────────────────
# ✅ Application Generator (Preview + PDF-ready)
# ─────────────────────────────────────────────
@api_routes.route("/application", methods=["GET", "POST"], endpoint="application")
def application_generator_view():
    if request.method == "POST":
        name = request.form.get("name")
        purpose = request.form.get("purpose")
        session_id = request.form.get("session_id", type=int)
        session = Session.query.get(session_id)
        session_name = session.name if session else "Unknown"

        application_text = f"""
        To Whom It May Concern,

        I, {name}, student of session {session_name}, am writing to request the following:
        {purpose}

        Sincerely,
        {name}
        """

        return render_template("application_preview.html", application=application_text, name=name, session_name=session_name, now=datetime.now())

    sessions = Session.query.order_by(Session.name.asc()).all()
    return render_template("application_form.html", sessions=sessions)

# ─────────────────────────────────────────────
# ✅ Application PDF Export (Optional)
# ─────────────────────────────────────────────
@api_routes.route("/application/pdf", methods=["POST"], endpoint="application_pdf")
def generate_application_pdf():
    name = request.form.get("name")
    purpose = request.form.get("purpose")
    session_name = request.form.get("session_name")
    now = datetime.now()

    application_text = f"""
    To Whom It May Concern,

    I, {name}, student of session {session_name}, am writing to request the following:
    {purpose}

    Sincerely,
    {name}
    """

    html = render_template("application_pdf.html", application=application_text, now=now)
    pdf = BytesIO()
    pisa.CreatePDF(html, dest=pdf)
    pdf.seek(0)
    return send_file(pdf, download_name="application.pdf", as_attachment=True)


# ─────────────────────────────────────────────
# ✅ Testimonial Dashboard Archive View
# ─────────────────────────────────────────────
@api_routes.route("/testimonial", methods=["GET"], endpoint="testimonial_dashboard")
def testimonial_dashboard_view():
    students = db.session.query(Student).join(Session).order_by(Session.name.asc(), Student.roll.asc()).all()
    return render_template("testimonial_dashboard.html", students=students)



@api_routes.route("/testimonial/<string:roll>/download", endpoint="download_testimonial_pdf")
def download_testimonial_pdf(roll):
    student = Student.query.filter_by(roll=roll).first_or_404()
    date = datetime.today().strftime("%d %B %Y")
    logo_path = url_for('static', filename='images/logo.png')

    html = render_template("testimonial_pdf.html",
        student_name=student.name,
        father_name=student.father_name,
        mother_name=student.mother_name,
        session=student.session,
        passing_year=student.pass_year,
        cgpa=student.cgpa,
        roll=student.roll,
        date=date,
        logo_path=logo_path
    )

    pdf = BytesIO()
    pisa.CreatePDF(html, dest=pdf)
    pdf.seek(0)
    return send_file(pdf, download_name=f"testimonial_{student.roll}.pdf", as_attachment=True)


# ─────────────────────────────────────────────
# ✅ Session-wise Testimonial Dashboard View
# ─────────────────────────────────────────────
@api_routes.route("/testimonial/session/<int:session_id>", methods=["GET"], endpoint="session_dashboard_view")
def session_dashboard_view(session_id):
    # 🔍 Get the selected session instance
    selected_session = Session.query.get_or_404(session_id)

    # ✅ Filter students using session_id (not relationship)
    students = Student.query.filter_by(session_id=selected_session.id).order_by(Student.roll.asc()).all()

    # 📅 Optional: current date for footer or PDF
    current_date = datetime.today().strftime("%d %B %Y")

    # 🖼️ Render dashboard with filtered students
    return render_template(
        "testimonial_dashboard.html",
        students=students,
        session=selected_session,
        current_date=current_date
    )



# 🔹 Districts with coordinates
districts = {
    "Kushtia": (23.9010, 89.1220),
    "Jessore": (23.1700, 89.2000),
    "Khulna": (22.8456, 89.5403),
    "Dhaka": (23.8103, 90.4125),
    "Rajshahi": (24.3745, 88.6042),
    "Barisal": (22.7010, 90.3535)
}

# 🔹 Forecast fetcher
def get_forecast_open_meteo(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset&timezone=Asia/Dhaka"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get("daily")
    except requests.exceptions.RequestException as e:
        print(f"❌ Forecast fetch failed: {e}")
    return None

# 🔹 Forecast route
@api_routes.route("/forecast", methods=["GET"], endpoint="forecast")
def forecast_view():
    selected = request.args.get("location", "Khulna")
    lat, lon = districts.get(selected, (22.8456, 89.5403))
    forecast_data = get_forecast_open_meteo(lat, lon)
    return render_template("forecast.html", forecast=forecast_data, districts=list(districts.keys()), selected=selected)