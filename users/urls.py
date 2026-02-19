from django.urls import path
from . import views

urlpatterns = [
    path('signup/patient/', views.patient_signup_view, name='patient_signup'),
    path('signup/doctor/', views.doctor_signup_view, name='doctor_signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
]

