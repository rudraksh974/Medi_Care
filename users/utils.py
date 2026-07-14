import random
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache

def send_otp_email(email):
    otp = str(random.randint(100000, 999999))
    cache.set(f"otp_{email}", otp, timeout=300)

    subject = "Your OTP for MediCare Signup"
    message = f"Your OTP is {otp}"

    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        print("Email sent successfully")
        return otp

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("EMAIL ERROR:", repr(e))
        return None