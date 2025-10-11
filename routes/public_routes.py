from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file,session as flask_session, current_app
from datetime import datetime, timezone
import requests, random, time
from io import BytesIO
from xhtml2pdf import pisa
from models import Notice, CalendarUpload, Student, db, Teacher, Course
from flask_mail import Message

public_routes = Blueprint("public_routes", __name__)


@public_routes.route("/", endpoint="home")
def home():
    return render_template("home.html")

# 🌤️ District coordinates for weather forecast
district_coords = {
    "Dhaka": (23.8103, 90.4125),
    "Khulna": (22.8456, 89.5403),
    "Chattogram": (22.3569, 91.7832),
    "Rajshahi": (24.3745, 88.6042),
    "Sylhet": (24.8949, 91.8687),
    "Barisal": (22.7010, 90.3535),
    "Rangpur": (25.7482, 89.2390),
    "Mymensingh": (24.7471, 90.4203),
    "Jessore": (23.1700, 89.2000),
    "Comilla": (23.4607, 91.1809),
    "Cox's Bazar": (21.4272, 92.0058),
    "Bogra": (24.8465, 89.3776),
    "Pabna": (24.0064, 89.2331),
    "Noakhali": (22.8236, 91.0973),
    "Narayanganj": (23.6238, 90.5000),
    "Tangail": (24.2513, 89.9167),
    "Jamalpur": (24.9375, 89.9370),
    "Satkhira": (22.7185, 89.0706),
    "Kushtia": (23.9017, 89.1220)
}

@public_routes.route("/weather", methods=["GET"], endpoint="forecast_view")
def forecast_view():
    location = request.args.get("location") or "Kushtia"
    selected = location
    forecast = {}
    lat, lon = district_coords.get(location, (23.9017, 89.1220))

    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset"
        f"&timezone=Asia/Dhaka"
    )

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        daily = data.get("daily", {})
        required_keys = ["time", "temperature_2m_max", "temperature_2m_min", "sunrise", "sunset"]
        if all(k in daily and isinstance(daily[k], list) and daily[k] for k in required_keys):
            forecast = daily
        else:
            flash("⚠️ Forecast data is incomplete. Please try again later.", "warning")
    except Exception as e:
        print(f"⚠️ API error for {location}: {e}")
        flash("⚠️ Unable to retrieve weather data. Please check your connection or try again later.", "warning")

    return render_template("weather.html", forecast=forecast, selected=selected, districts=list(district_coords.keys()))
####################################################################################################################################

# ✅ Public Notice Viewer
@public_routes.route("/notice", methods=["GET"])
def notice_view():
    now = datetime.now(timezone.utc)
    notices = Notice.query.filter(
        (Notice.expires_at == None) | (Notice.expires_at > now)
    ).order_by(Notice.created_at.desc()).all()

    return render_template("public/notice.html", notices=notices)

# ✅ Academic Calendar Viewer (Session-wise)
@public_routes.route("/calendar/<session>", methods=["GET"])
def calendar_view(session):
    calendar = CalendarUpload.query.filter_by(session=session).first()

    if not calendar:
        flash("No calendar found for this session.", "warning")
        return render_template("public/calendar.html", calendar=None, session=session)

    return render_template("public/calendar.html", calendar=calendar, session=session)


@public_routes.route("/calendar", methods=["GET", "POST"])
def calendar_list():
    all_sessions = [c.session for c in CalendarUpload.query.order_by(CalendarUpload.session).all()]
    selected_session = None

    if request.method == "POST":
        selected_session = request.form.get("session")
        calendars = CalendarUpload.query.filter_by(session=selected_session).order_by(CalendarUpload.session).all()
    else:
        calendars = CalendarUpload.query.order_by(CalendarUpload.session).all()

    return render_template("public/calendar_list.html", calendars=calendars, sessions=all_sessions, selected_session=selected_session)















# ─────────────────────────────────────────────
# ✅ Document Generator
# ─────────────────────────────────────────────
@public_routes.route("/generate", methods=["GET", "POST"], endpoint="generate")
def generate_document_view():
    if request.method == "POST":
        name = request.form.get("name")
        role = request.form.get("role")
        roll = request.form.get("roll")
        registration = request.form.get("registration")
        academic_session = request.form.get("session")
        recipient = request.form.get("recipient")
        subject = request.form.get("subject")
        request_type = request.form.get("request_type", "").lower()
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        return render_template(
            "public/document_preview.html",
            name=name,
            role=role,
            roll=roll,
            registration=registration,
            academic_session=academic_session,
            recipient=recipient,
            subject=subject,
            request_type=request_type,
            start_date=start_date,
            end_date=end_date,
            now=datetime.now()
        )

    return render_template("public/document_form.html")

# ─────────────────────────────────────────────
# ✅ Document PDF Export
# ─────────────────────────────────────────────
@public_routes.route("/document/pdf", methods=["POST"], endpoint="generate_document_pdf")
def generate_document_pdf():
    academic_session = request.form.get("session") or "Not Provided"

    html = render_template(
        "document_pdf.html",
        name=request.form.get("name"),
        role=request.form.get("role"),
        roll=request.form.get("roll"),
        registration=request.form.get("registration"),
        academic_session=academic_session,
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
    return send_file(pdf, download_name="public/generated_document.pdf", as_attachment=True)






















@public_routes.route("/students", methods=["GET"])
def student_panel():
    selected_session = request.args.get("session", "")
    query = Student.query
    if selected_session:
        query = query.filter_by(session=selected_session)
    students = query.order_by(Student.roll.asc()).all()

    # 🔍 Only sessions that have students
    sessions_raw = db.session.query(Student.session).distinct().order_by(Student.session.asc()).all()
    sessions = [s[0] for s in sessions_raw if s[0]]

    return render_template("public/student_panel.html", students=students, sessions=sessions, selected_session=selected_session)

@public_routes.route("/students", methods=["GET"])
def student_list():
    students = Student.query.order_by(Student.roll.asc()).all()
    return render_template("public/student_list.html", students=students)






















# ─────────────────────────────────────────────────────────────
# ✅ Teacher Login
# ─────────────────────────────────────────────────────────────

@public_routes.route("/student-login", methods=["GET", "POST"], endpoint="student_login")
def student_login():
    return render_template("student_login.html")



@public_routes.route("/teacher/login", methods=["GET", "POST"], endpoint="teacher_login")
def teacher_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        teacher = Teacher.query.filter_by(email=email).first()
        if not teacher or not teacher.check_password(password):
            flash("⚠️ Invalid email or password.", "danger")
            return redirect(url_for("public_routes.teacher_login"))

        session["teacher_id"] = teacher.id
        flash(f"✅ Welcome back, {teacher.name}!", "success")
        return redirect(url_for("public_routes.teacher_panel"))

    return render_template("public/teacher_login.html")




# ✅ Request OTP
@public_routes.route("/teacher/request-otp", methods=["GET", "POST"])
def request_otp():
    if request.method == "POST":
        email = request.form.get("email")
        teacher = Teacher.query.filter_by(email=email).first()

        if not teacher:
            flash("❌ Email not found. Contact admin.", "danger")
            return redirect(url_for("public_routes.request_otp"))

        otp = str(random.randint(100000, 999999))
        session["otp_email"] = email
        session["otp_code"] = otp
        session["otp_expiry"] = time.time() + 300

        try:
            msg = Message(
                subject="🔐 Your OTP for Teacher Registration",
                sender=current_app.config["MAIL_USERNAME"],
                recipients=[email],
                body=f"""Dear {teacher.name},

Your OTP is: {otp}

This code will expire in 5 minutes.

Regards,
Academic Gateway"""
            )
            # ✅ Safe fallback: use mail object directly
            mail.send(msg)
            flash("📩 OTP sent to your email.", "info")
        except Exception as e:
            print("❌ Email send error:", type(e)._name_, str(e))
            flash("⚠️ Failed to send email. Try again or contact admin.", "danger")

        return redirect(url_for("public_routes.verify_otp"))

    return render_template("public/request_otp.html")

# ✅ Verify OTP & Set Password
@public_routes.route("/teacher/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form.get("otp")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if password != confirm:
            flash("❌ Passwords do not match.", "danger")
            return redirect(url_for("public_routes.verify_otp"))

        if time.time() > session.get("otp_expiry", 0):
            session.pop("otp_code", None)
            session.pop("otp_expiry", None)
            flash("⏰ OTP expired. Please request a new one.", "warning")
            return redirect(url_for("public_routes.request_otp"))

        if entered_otp != session.get("otp_code"):
            flash("❌ Invalid OTP.", "danger")
            return redirect(url_for("public_routes.verify_otp"))

        email = session.get("otp_email")
        teacher = Teacher.query.filter_by(email=email).first()
        if not teacher:
            flash("❌ Teacher not found.", "danger")
            return redirect(url_for("public_routes.request_otp"))

        teacher.set_password(password)
        db.session.commit()

        session.pop("otp_email", None)
        session.pop("otp_code", None)
        session.pop("otp_expiry", None)

        flash("✅ Password set successfully. You can now login.", "success")
        return redirect(url_for("public_routes.teacher_login"))

    return render_template("public/verify_otp.html")
# ─────────────────────────────────────────────────────────────
# ✅ Teacher Panel
# ─────────────────────────────────────────────────────────────
@public_routes.route("/teacher/panel", endpoint="teacher_panel")
def teacher_panel():
    teacher_id = session.get("teacher_id")
    if not teacher_id:
        flash("🔒 Please login to access your panel.", "warning")
        return redirect(url_for("public_routes.teacher_login"))

    teacher = Teacher.query.get_or_404(teacher_id)
    return render_template("public/teacher_panel.html", teacher=teacher)


# ─────────────────────────────────────────────────────────────
# ✅ Logout
# ─────────────────────────────────────────────────────────────
@public_routes.route("/teacher/logout", endpoint="teacher_logout")
def teacher_logout():
    session.pop("teacher_id", None)
    flash("👋 Logged out successfully.", "info")
    return redirect(url_for("public_routes.teacher_login"))


# ─────────────────────────────────────────────────────────────
# ✅ View Assigned Courses
# ─────────────────────────────────────────────────────────────
@public_routes.route("/teacher/courses", endpoint="teacher_courses")
def teacher_courses():
    if "teacher_id" not in session:
        flash("🔒 Please login to access your courses.", "warning")
        return redirect(url_for("public_routes.teacher_login"))

    teacher = Teacher.query.get(session["teacher_id"])
    if not teacher:
        flash("❌ Teacher not found.", "danger")
        return redirect(url_for("public_routes.teacher_login"))

    courses = teacher.courses.order_by(Course.name.asc()).all()
    return render_template("teacher_courses.html", teacher=teacher, courses=courses)