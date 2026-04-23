from locust import HttpUser, task, between

class AcademicUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # ✅ Match Flask login form: username + password
        self.client.post("/admin/login", data={
            "username": "statadmin",
            "password": "admin1922025"
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})

    @task(2)
    def view_dashboard(self):
        self.client.get("/admin/dashboard")

    @task(1)
    def generate_document(self):
        self.client.post("/admin/generate-document", data={
            "template_id": "grade_report",
            "student_id": "S123"
        }, headers={"Content-Type": "application/x-www-form-urlencoded"})
