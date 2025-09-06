from flask import Flask
from extensions import db, login_manager
from routes.api_routes import api_routes
from routes.auth_routes import auth_routes
from models import User

from flask_login import LoginManager

app = Flask(__name__)
app.secret_key = "your_secret_key"

# 🔹 Database Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gateway.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 🔹 Initialize Extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "auth.login"

# 🔹 User Loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 🔹 Register Blueprints
app.register_blueprint(api_routes, url_prefix="/")
app.register_blueprint(auth_routes, url_prefix="/auth")

# 🔹 Run App
if __name__ == "__main__":
    app.run(debug=True)