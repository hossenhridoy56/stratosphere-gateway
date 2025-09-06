from datetime import datetime

def render_document(data):
    recipient = data.get("recipient") or "Principal"
    subject = data.get("subject") or "Application"
    name = data.get("name") or "Student Name"
    role = data.get("role") or "student"
    request_type = data.get("request_type") or "general"
    start_date = data.get("start_date") or "N/A"
    end_date = data.get("end_date") or "N/A"
    roll = data.get("roll") or "N/A"
    registration = data.get("registration") or "N/A"
    session = data.get("session") or "N/A"
    generated_on = datetime.now().strftime("%d %B, %Y")

    body = ""

    if request_type == "recommendation":
        body = f"""
<p>I hope this message finds you well. I am writing to request a recommendation letter to support my application 
for academic or professional purposes.</p>
<p>As a student of your department, I have always strived to maintain a high standard of performance and integrity. 
Your endorsement would be invaluable in highlighting my qualifications and character.</p>
<p>I would be honored if you could provide this letter at your convenience. 
Please let me know if you require any specific details or documents.</p>
<p>Thank you for your time and support.</p>
"""

    elif request_type == "leave":
        body = f"""
<p>I am <strong>{name}</strong>, working as a <strong>{role}</strong>. I would like to request leave from 
<strong>{start_date}</strong> to <strong>{end_date}</strong>.</p>
<p>The reason for this leave falls under the category of <strong>Leave</strong>.</p>
<p>I kindly request you to consider my application and grant me leave for the mentioned period.</p>
"""

    elif request_type == "certificate":
        body = f"""
<p>I am <strong>{name}</strong>, serving as a <strong>{role}</strong>. I am writing to formally request a certificate 
for the period from <strong>{start_date}</strong> to <strong>{end_date}</strong>.</p>
<p>This certificate is required for official purposes.</p>
<p>I would be grateful if you could issue the certificate at your earliest convenience.</p>
"""

    else:
        body = f"""
<p>I am <strong>{name}</strong>, working as a <strong>{role}</strong>. I am submitting this application for your kind consideration.</p>
<p>The requested period is from <strong>{start_date}</strong> to <strong>{end_date}</strong>.</p>
<p>This request falls under the category of <strong>{request_type}</strong>.</p>
"""

    return f"""
<p><strong>To:</strong><br>{recipient}<br>Department of Statistics<br>Islamic University, Kushtia</p>
<br>
<p><strong>Subject:</strong> <strong>{subject}</strong></p>
<br>
<p>Dear Sir/Madam,</p>
{body}
<br>
<p>Sincerely,<br>
<strong>{name}</strong><br>
Roll: {roll}<br>
Registration: {registration}<br>
Session: {session}<br>
{role}<br>(Signature)</p>
<br>
<p><strong>Generated on:</strong> {generated_on}</p>
"""