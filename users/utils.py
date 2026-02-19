import random
from django.core.mail import send_mail
from django.conf import settings

def send_otp_email(email):
    otp = str(random.randint(100000, 999999))
    subject = 'Your OTP for MediCare Signup'
    message = f'Your OTP for verifying your email is: {otp}'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    
    try:
        send_mail(subject, message, email_from, recipient_list)
        return otp
    except Exception as e:
        print(f"Error sending email: {e}")
        return None
