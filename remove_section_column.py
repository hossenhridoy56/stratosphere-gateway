import sqlite3

db_path = "gateway.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# ✅ Step 0: যদি student_new আগে থেকেই থাকে, তাহলে drop করে দাও
cursor.execute("DROP TABLE IF EXISTS student_new")

# ✅ Step 1: নতুন table তৈরি করো section_id বাদ দিয়ে
cursor.execute("""
CREATE TABLE student_new (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    roll TEXT UNIQUE NOT NULL,
    reg TEXT,
    mobile TEXT,
    email TEXT,
    department TEXT,
    father_name TEXT,
    mother_name TEXT,
    cgpa TEXT,
    pass_year TEXT,
    session TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1
)
""")

# ✅ Step 2: পুরনো student data কপি করো
cursor.execute("""
INSERT INTO student_new (id, name, roll, reg, mobile, email, department, father_name, mother_name, cgpa, pass_year, session, is_active)
SELECT id, name, roll, reg, mobile, email, department, father_name, mother_name, cgpa, pass_year, session, is_active FROM student
""")

# ✅ Step 3: পুরনো table drop করো
cursor.execute("DROP TABLE student")

# ✅ Step 4: নতুন table rename করো
cursor.execute("ALTER TABLE student_new RENAME TO student")

conn.commit()
conn.close()

print("✅ section_id column removed successfully.")