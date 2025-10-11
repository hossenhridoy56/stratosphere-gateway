from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps

# ✅ Step 1: Blueprint setup
auth_routes = Blueprint("auth_routes", __name__)

# ✅ Step 2: Fixed admin credentials
ADMIN_USERNAME = "statadmin"
ADMIN_PASSWORD = "admin1922025"

# ✅ Step 3: Admin login route
@auth_routes.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["role"] = "admin"
            flash("✅ Logged in as Admin.", "success")
            return redirect(url_for("admin_routes.admin_dashboard"))
        else:
            flash("❌ Invalid credentials.", "danger")

    return render_template("auth/admin_login.html")

# ✅ Step 4: Admin route protection decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "admin":
            flash("❌ Admin access required.", "danger")
            return redirect(url_for("auth_routes.admin_login"))
        return f(*args, **kwargs)
    return decorated_function

# ✅ Step 5: Logout route (optional but useful)
@auth_routes.route("/logout")
def logout():
    session.clear()
    flash("👋 Logged out successfully.", "info")
    return redirect(url_for("auth_routes.admin_login"))