from django.urls import path
from . import views

urlpatterns = [
    path('book/<int:doctor_id>/', views.book_appointment, name='book_appointment'),
    path('patient/', views.patient_appointments, name='patient_appointments'),
    path('doctor/', views.doctor_appointments, name='doctor_appointments'),
    path('update/<int:appointment_id>/', views.update_appointment_status, name='update_appointment_status'),
]
