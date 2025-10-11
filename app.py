from flask import Flask, render_template, send_from_directory
from flask_migrate import Migrate
from flask_mail import Mail
from models import db, CalendarUpload

# ✅ Create Flask app
app = Flask(__name__)

# ✅ Secret key
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with a secure key in production

# ✅ Database config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stratosphere.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ Mail config (Gmail + App Password)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "hossenhridoy56@gmail.com"  # ✅ Replace with your Gmail
app.config["MAIL_PASSWORD"] = "runh jbss ryxj yazv"        # ✅ Replace with your App Password

# ✅ Bind extensions
db.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)

# ✅ Register Blueprints
from routes.public_routes import public_routes
from routes.admin_routes import admin_routes
from routes.auth_routes import auth_routes
from routes.teacher_routes import teacher_routes

app.register_blueprint(public_routes)
app.register_blueprint(admin_routes, url_prefix="/admin")
app.register_blueprint(auth_routes)
app.register_blueprint(teacher_routes)

# ✅ Home route
@app.route("/", methods=["GET"])
def home():
    try:
        return render_template("home.html")
    except Exception as e:
        print("🔴 Template Error:", e)
        return "Template not found", 500

# ✅ Serve uploaded files (outside static folder)
@app.route("/uploads/<path:filename>")
def serve_uploaded_file(filename):
    try:
        return send_from_directory("uploads", filename)
    except Exception as e:
        print("🔴 File Serve Error:", e)
        return "File not found", 404

# ✅ Run server
if __name__ == "__main__":
    print("🚀 Starting Flask server...")
    app.run(debug=True)