from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
from io import BytesIO
import os

from xhtml2pdf import pisa


from routes.auth_routes import admin_required  # ✅ Protect with session

admin_routes = Blueprint("admin_routes", __name__)

from models import db, CalendarUpload, Notice, Student, Teacher, Course
from routes.auth_routes import admin_required

admin_routes = Blueprint("admin_routes", __name__, url_prefix="/admin")
admin_routes = Blueprint("admin_routes", __name__)

UPLOAD_CALENDAR_FOLDER = "static/uploads/calendars"
UPLOAD_NOTICE_FOLDER = "static/uploads/notices"

# 🔧 Generate stitched session list
def generate_sessions(start_year=2009, count=100):
    return [f"{y}-{y+1}" for y in range(start_year, start_year + count)]

# 📊 Admin Dashboard
@admin_routes.route("/dashboard", methods=["GET"], endpoint="admin_dashboard")
@admin_required
def admin_dashboard():
    notices = Notice.query.order_by(Notice.created_at.desc()).all()
    calendars = CalendarUpload.query.order_by(CalendarUpload.session.desc()).all()
    return render_template("admin/dashboard.html", notices=notices, calendars=calendars)

# ➕ Add Student (Manual + Bulk)
@admin_routes.route("/student/add", methods=["GET", "POST"])
@admin_required
def add_student():
    sessions = generate_sessions()

    if request.method == "POST":
        # 🔹 Manual Entry
        if request.form.get("roll"):
            session_name = request.form.get("session", "").strip()
            department = request.form.get("department", "").strip() or "—"

            student = Student(
                roll=request.form.get("roll", "").strip(),
                name=request.form.get("name", "").strip(),
                session=session_name,
                department=department,
                email=request.form.get("email", "").strip(),
                mobile=request.form.get("mobile", "").strip(),
                father_name=request.form.get("father_name", "").strip(),
                mother_name=request.form.get("mother_name", "").strip(),
                pass_year=request.form.get("pass_year", "").strip(),
                cgpa=request.form.get("cgpa", "").strip()
            )

            # ✅ stitched course binding
            course = Course.query.filter_by(session=session_name).first()
            if course:
                student.courses.append(course)

            try:
                db.session.add(student)
                db.session.commit()
                flash("✅ Student added successfully.", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"❌ Failed to add student: {str(e)}", "danger")

            return redirect(url_for("admin_routes.add_student"))

        # 🔹 Bulk Upload
        elif request.files.get("student_file"):
            file = request.files["student_file"]
            session_selected = request.form.get("upload_session")

            if not session_selected:
                flash("❌ Session is required for file upload.", "danger")
                return redirect(url_for("admin_routes.add_student"))

            try:
                import pandas as pd
                df = pd.read_csv(file) if file.filename.endswith(".csv") else pd.read_excel(file)
                df = df.fillna("").astype(str)
                df.columns = [col.lower().strip() for col in df.columns]

                success_count = 0
                duplicate_count = 0

                # ✅ stitched course fetch once
                course = Course.query.filter_by(session=session_selected).first()

                for _, row in df.iterrows():
                    roll = row.get("roll", "").strip()
                    name = row.get("name", "").strip()
                    department = row.get("department", "").strip() or "—"

                    if not roll or not name:
                        continue

                    if Student.query.filter_by(roll=roll).first():
                        duplicate_count += 1
                        continue

                    student = Student(
                        roll=roll,
                        name=name,
                        session=session_selected,
                        department=department,
                        email=row.get("email", "").strip(),
                        mobile=row.get("mobile", "").strip(),
                        father_name=row.get("father_name", "").strip(),
                        mother_name=row.get("mother_name", "").strip(),
                        pass_year=row.get("pass_year", "").strip(),
                        cgpa=row.get("cgpa", "").strip()
                    )

                    # ✅ stitched course binding
                    if course:
                        student.courses.append(course)

                    db.session.add(student)
                    success_count += 1

                db.session.commit()
                flash(f"✅ {success_count} students uploaded successfully.", "success")
                if duplicate_count:
                    flash(f"⚠️ {duplicate_count} duplicate rolls skipped.", "warning")

            except Exception as e:
                db.session.rollback()
                flash(f"❌ Upload failed: {str(e)}", "danger")

            return redirect(url_for("admin_routes.add_student"))

    return render_template("admin/student_add.html", sessions=sessions)

# 📋 Student List
@admin_routes.route("/student/list", methods=["GET"])
@admin_required
def student_list():
    selected_session = request.args.get("session", "")
    
    # 🔍 Filter students by selected session
    query = Student.query
    if selected_session:
        query = query.filter_by(session=selected_session)
    students = query.order_by(Student.roll.asc()).all()

    # 🧠 Only show sessions that have students
    sessions_raw = db.session.query(Student.session).distinct().order_by(Student.session.asc()).all()
    sessions = [s[0] for s in sessions_raw if s[0]]  # Flatten and remove nulls

    return render_template(
        "admin/student_list.html",
        students=students,
        sessions=sessions,
        selected_session=selected_session
    )

# ✏️ Edit Student
@admin_routes.route("/student/edit/<string:roll>", methods=["GET", "POST"])
@admin_required
def edit_student(roll):
    student = Student.query.filter_by(roll=roll).first_or_404()
    sessions = generate_sessions()

    if request.method == "POST":
        student.name = request.form.get("name")
        student.session = request.form.get("session")
        student.email = request.form.get("email")
        student.mobile = request.form.get("mobile")
        student.father_name = request.form.get("father_name")
        student.mother_name = request.form.get("mother_name")
        student.pass_year = request.form.get("pass_year")
        student.cgpa = request.form.get("cgpa")
        db.session.commit()
        flash("✅ Student information updated successfully.", "success")
        return redirect(url_for("admin_routes.student_list"))

    return render_template("admin/edit_student.html", student=student, sessions=sessions)

# 🗑️ Delete Student
@admin_routes.route("/student/delete/<string:roll>", methods=["POST"])
@admin_required
def delete_student(roll):
    student = Student.query.filter_by(roll=roll).first_or_404()
    db.session.delete(student)
    db.session.commit()
    flash("🗑️ Student deleted successfully.", "success")
    return redirect(url_for("admin_routes.student_list"))

# 📤 Export Students
@admin_routes.route("/student/export", methods=["GET"])
def export_students():
    session_name = request.args.get("session", "")
    export_format = request.args.get("format", "pdf")

    query = Student.query
    if session_name:
        query = query.filter_by(session=session_name)
    students = query.order_by(Student.roll.asc()).all()

    if not students:
        flash(f"⚠️ No students found for session '{session_name}'.", "warning")
        return redirect(url_for("public_routes.student_panel"))

    if export_format == "pdf":
        # 🔧 Placeholder for PDF logic
        return f"📄 PDF export for session {session_name} with {len(students)} students"
    
    elif export_format == "excel":
        # 🔧 Placeholder for Excel logic
        return f"📊 Excel export for session {session_name} with {len(students)} students"
    
    else:
        flash("❌ Invalid export format.", "danger")
        return redirect(url_for("public_routes.student_panel"))
    







# ─────────────────────────────────────────────────────────────
# ✅ Add Teacher
# ─────────────────────────────────────────────────────────────

@admin_routes.route("/teacher/add", methods=["GET", "POST"], endpoint="add_teacher")
def add_teacher():
    if request.method == "GET":
        return render_template("admin/add_teacher.html")

    name = request.form.get("name")
    designation = request.form.get("designation")
    email = request.form.get("email")
    password = request.form.get("password")
    mobile = request.form.get("mobile")
    department = request.form.get("department")
    joining_date_raw = request.form.get("joining_date")
    joining_date = datetime.strptime(joining_date_raw, "%Y-%m-%d") if joining_date_raw else None

    if not name or not email or not password:
        flash("⚠️ Name, email, and password are required.", "warning")
        return redirect(url_for("admin_routes.teacher_panel"))

    existing = Teacher.query.filter_by(email=email).first()
    if existing:
        flash("❌ Email already exists. Try another.", "danger")
        return redirect(url_for("admin_routes.teacher_panel"))

    new_teacher = Teacher(
        name=name,
        designation=designation,
        email=email,
        mobile=mobile,
        department=department,
        joining_date=joining_date
    )
    new_teacher.set_password(password)
    db.session.add(new_teacher)
    db.session.commit()

    flash(f"✅ Teacher '{name}' added successfully.", "success")
    return redirect(url_for("admin_routes.teacher_panel"))

# ─────────────────────────────────────────────────────────────
# ✅ Teacher List
# ─────────────────────────────────────────────────────────────
@admin_routes.route("/teacher/panel", methods=["GET"], endpoint="teacher_panel")
def teacher_panel():
    teachers = Teacher.query.order_by(Teacher.name.asc()).all()
    return render_template("admin/teacher_panel.html", teachers=teachers)

# ─────────────────────────────────────────────────────────────
# ✅ Edit Teacher
# ─────────────────────────────────────────────────────────────
@admin_routes.route("/teacher/edit/<int:id>", methods=["GET", "POST"], endpoint="edit_teacher")
def edit_teacher(id):
    teacher = Teacher.query.get_or_404(id)

    if request.method == "POST":
        teacher.name = request.form.get("name")
        teacher.email = request.form.get("email")
        teacher.mobile = request.form.get("mobile")
        teacher.department = request.form.get("department")
        teacher.designation = request.form.get("designation")

        joining_date_str = request.form.get("joining_date")
        try:
            teacher.joining_date = datetime.strptime(joining_date_str, "%Y-%m-%d").date() if joining_date_str else None
        except ValueError:
            flash("⚠️ Invalid joining date format.", "danger")
            return redirect(url_for("admin_routes.edit_teacher", id=id))

        db.session.commit()
        flash("✅ Teacher updated successfully.", "success")
        return redirect(url_for("admin_routes.teacher_panel"))

    return render_template("admin/edit_teacher.html", teacher=teacher)

# ─────────────────────────────────────────────────────────────
# ✅ Delete Teacher
# ─────────────────────────────────────────────────────────────
@admin_routes.route("/teacher/delete/<int:id>", methods=["POST"], endpoint="delete_teacher")
def delete_teacher(id):
    teacher = Teacher.query.get_or_404(id)
    db.session.delete(teacher)
    db.session.commit()
    flash("🗑️ Teacher deleted successfully.", "success")
    return redirect(url_for("admin_routes.teacher_panel"))
















































########################################################################################################

# 📅 Calendar Upload
@admin_routes.route("/calendar/upload", methods=["GET", "POST"])
@admin_required
def upload_calendar():
    sessions = generate_sessions()

    if request.method == "POST":
        selected_session = request.form.get("session")
        file = request.files.get("calendar_file")

        if not selected_session or not file:
            flash("❌ Session and file are required.", "danger")
            return redirect(url_for("admin_routes.upload_calendar"))

        file_name = secure_filename(file.filename)
        upload_path = os.path.join(UPLOAD_CALENDAR_FOLDER, file_name)

        try:
            file.save(upload_path)
            calendar = CalendarUpload(session=selected_session, filename=file_name)
            db.session.add(calendar)
            db.session.commit()
            flash(f"✅ Calendar uploaded for session {selected_session}.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Upload failed: {str(e)}", "danger")

        return redirect(url_for("admin_routes.upload_calendar"))

    return render_template("admin/calendar_upload.html", sessions=sessions)

# ✏️ Calendar Edit
@admin_routes.route("/calendar/edit/<int:calendar_id>", methods=["GET", "POST"], endpoint="edit_calendar")
@admin_required
def edit_calendar(calendar_id):
    calendar = CalendarUpload.query.get_or_404(calendar_id)
    sessions = generate_sessions()

    if request.method == "POST":
        new_session = request.form.get("session")
        new_file = request.files.get("calendar_file")

        if new_session:
            calendar.session = new_session

        if new_file and new_file.filename:
            old_path = os.path.join(UPLOAD_CALENDAR_FOLDER, calendar.filename)
            if os.path.exists(old_path):
                os.remove(old_path)

            new_filename = secure_filename(new_file.filename)
            new_path = os.path.join(UPLOAD_CALENDAR_FOLDER, new_filename)
            new_file.save(new_path)
            calendar.filename = new_filename

        try:
            db.session.commit()
            flash("✏️ Calendar updated successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"❌ Update failed: {str(e)}", "danger")

        return redirect(url_for("admin_routes.admin_dashboard"))

    return render_template("admin/calendar_edit.html", calendar=calendar, sessions=sessions)

# 🗑️ Calendar Delete
@admin_routes.route("/calendar/delete/<int:calendar_id>", methods=["POST"], endpoint="delete_calendar")
@admin_required
def delete_calendar(calendar_id):
    calendar = CalendarUpload.query.get_or_404(calendar_id)
    file_path = os.path.join(UPLOAD_CALENDAR_FOLDER, calendar.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(calendar)
    db.session.commit()
    flash("🗑️ Calendar deleted successfully.", "success")
    return redirect(url_for("admin_routes.admin_dashboard"))

# 📢 Notice Upload
@admin_routes.route("/notice/upload", methods=["GET", "POST"])
@admin_required
def notice_upload():
    if request.method == "POST":
        title = request.form.get("title")
        expires_at = request.form.get("expires_at")
        file = request.files.get("notice_file")

        if not file or not title:
            flash("❌ Title and file are required.", "danger")
            return redirect(url_for("admin_routes.notice_upload"))

        file_type = file.filename.rsplit('.', 1)[-1].lower()
        file_name = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_NOTICE_FOLDER, file_name))

        notice = Notice(
            title=title,
            file_type=file_type,
            file_name=file_name,
            expires_at=datetime.strptime(expires_at, "%Y-%m-%d") if expires_at else None
        )
        db.session.add(notice)
        db.session.commit()
        flash("✅ Notice uploaded successfully.", "success")
        return redirect(url_for("admin_routes.notice_upload"))

    return render_template("admin/notice_upload.html")

# 🗑️ Notice Delete
@admin_routes.route("/notice/delete/<int:notice_id>", methods=["POST"], endpoint="delete_notice")
@admin_required
def delete_notice(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    file_path = os.path.join(UPLOAD_NOTICE_FOLDER, notice.file_name)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(notice)
    db.session.commit()
    flash("🗑️ Notice deleted successfully.", "success")
    return redirect(url_for("admin_routes.admin_dashboard"))



############################################################################################

# ─────────────────────────────────────────────
# ✅ Testimonial Preview View
# ─────────────────────────────────────────────
@admin_routes.route("/testimonial/view/<string:roll>", endpoint="testimonial_view_page")
def testimonial_view_page(roll):
    student = Student.query.filter_by(roll=roll).first_or_404()
    context = {
        "student_name": student.name,
        "father_name": student.father_name,
        "mother_name": student.mother_name,
        "session_name": student.session,
        "passing_year": student.pass_year,
        "cgpa": student.cgpa,
        "date": datetime.today().strftime("%d %B %Y"),
        "roll": student.roll
    }
    return render_template("admin/testimonial_view.html", **context)

# ─────────────────────────────────────────────
# ✅ Testimonial PDF Download
# ─────────────────────────────────────────────
@admin_routes.route("/testimonial/<string:roll>/download", endpoint="download_testimonial_pdf_v2")
def download_testimonial_pdf_v2(roll):
    student = Student.query.filter_by(roll=roll).first_or_404()
    date = datetime.today().strftime("%d %B %Y")
    logo_path = url_for('static', filename='images/logo.png')

    html = render_template("admin/testimonial_pdf.html",
        student_name=student.name,
        father_name=student.father_name,
        mother_name=student.mother_name,
        session_name=student.session,
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
@admin_routes.route("/testimonial/archive", methods=["GET", "POST"], endpoint="testimonial_archive")
def testimonial_archive_view():
    selected_session = request.form.get("session")

    # ✅ stitched session list
    sessions = db.session.query(Student.session).distinct().order_by(Student.session.asc()).all()
    session_list = [s[0] for s in sessions if s[0]]

    # ✅ stitched student query
    students = []
    if selected_session:
        students = Student.query.filter(
            Student.session == selected_session,
            Student.pass_year.isnot(None)
        ).order_by(Student.roll.asc()).all()

    return render_template("admin/testimonial_archive.html",
        students=students,
        sessions=session_list,
        selected_session=selected_session,
        date=datetime.today().strftime("%Y")
    )





@admin_routes.route("/generate", methods=["GET", "POST"], endpoint="generate")
def generate():
    if request.method == "POST":
        # ✅ stitched form data
        student_name = request.form.get("student_name")
        father_name = request.form.get("father_name")
        mother_name = request.form.get("mother_name")
        session_name = request.form.get("session_name")
        passing_year = request.form.get("passing_year")
        cgpa = request.form.get("cgpa")
        roll = request.form.get("roll")

        # ✅ stitched context for preview
        context = {
            "student_name": student_name,
            "father_name": father_name,
            "mother_name": mother_name,
            "session_name": session_name,
            "passing_year": passing_year,
            "cgpa": cgpa,
            "roll": roll,
            "date": datetime.today().strftime("%d %B %Y")
        }

        return render_template("admin/testimonial_view.html", **context)

    # ✅ GET request — show form
    return render_template("admin/generate_form.html")







@admin_routes.route("/generate-document", methods=["POST"])
@admin_required
def generate_document():
    template_id = request.form.get("template_id")
    student_id = request.form.get("student_id")

    # ✅ Simulate document generation
    print(f"📄 Generating document: {template_id} for student {student_id}")
    return jsonify({"status": "success", "message": "Document generated"}), 200
