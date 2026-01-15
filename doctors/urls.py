from django.urls import path
from . import views

urlpatterns = [
    path('', views.doctor_list, name='doctor_list'),
    path('profile/edit/', views.edit_doctor_profile, name='edit_doctor_profile'),
]
