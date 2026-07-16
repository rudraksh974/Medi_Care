import random
import requests
from django.conf import settings

def send_otp_email(email):
    otp = str(random.randint(100000, 999999))

    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": settings.BREVO_API_KEY,
        "content-type": "application/json"
    }

    data = {
        "sender": {
            "name": "MediCare",
            "email": settings.DEFAULT_FROM_EMAIL
        },
        "to": [
            {
                "email": email
            }
        ],
        "subject": "Your OTP for MediCare Signup",
        "htmlContent": f"<h2>Your OTP is: {otp}</h2>"
    }

    response = requests.post(url, json=data, headers=headers)

    print(response.status_code)
    print(response.text)

    if response.status_code == 201:
        return otp

    return None
