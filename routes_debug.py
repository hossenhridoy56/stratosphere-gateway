from flask import Flask, request

app = Flask(__name__)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    return "Login route hit", 200

@app.route('/admin/dashboard')
def admin_dashboard():
    return "Dashboard route hit", 200

@app.route('/admin/generate-document', methods=['POST'])
def generate_document():
    return "Document generation route hit", 200

if __name__ == '__main__':
    app.run(debug=True)
