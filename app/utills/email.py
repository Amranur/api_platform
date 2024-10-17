import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(email: str,  subject: str, body: str):
    # SMTP server configuration
    smtp_host = "mail.sobjanta.ai"
    smtp_port = 587  # SSL/TLS port
    smtp_user = "sobjanta@sobjanta.ai"
    smtp_password = "!ry1wrI_cV@$"

    # Create the email
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Send the email
    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()  # Secure the connection
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, email, msg.as_string())
        server.quit()
        print("Verification email sent successfully")
    except Exception as e:
        print(f"Failed to send verification email: {e}")