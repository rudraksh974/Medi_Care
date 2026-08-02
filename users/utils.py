import random
import requests
from django.conf import settings

def send_otp_email(email):
    otp = str(random.randint(100000, 999999))
    api_key = getattr(settings, "BREVO_API_KEY", None) or getattr(settings, "ANYMAIL", {}).get("BREVO_API_KEY")

    if not api_key:
        print("BREVO_API_KEY is missing or not configured.")
        return None

    sender_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or "noreply@medicare.com"

    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    data = {
        "sender": {
            "name": "MediCare",
            "email": sender_email
        },
        "to": [
            {
                "email": email
            }
        ],
        "subject": "Your OTP for MediCare Signup",
        "htmlContent": f"<h2>Thank you for joining MediCare!<br>Your OTP is: {otp}<br>Please do not share this OTP with anyone.</h2>"
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        print(f"Brevo Status Code: {response.status_code}")
        print(f"Brevo Response: {response.text}")

        if response.status_code in [200, 201]:
            return otp
    except Exception as e:
        print(f"Error sending OTP email via Brevo: {e}")

    return None
