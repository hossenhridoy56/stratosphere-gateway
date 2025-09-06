from flask import Flask
from extensions import db
from routes import api_routes
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = "your_secret_key"

# 🔹 Use gateway.db to match your scripts and structure
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gateway.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 🔹 Initialize DB and Migrations
db.init_app(app)
migrate = Migrate(app, db)

# 🔹 Register routes
app.register_blueprint(api_routes, url_prefix="/")

# 🔹 Run the app
if __name__ == "__main__":
    app.run(debug=True)