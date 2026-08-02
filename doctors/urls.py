from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.doctor_list, name='doctor_list'),
    path('profile/edit/', views.edit_doctor_profile, name='edit_doctor_profile'),
    path('availability/', views.manage_availability, name='manage_availability'),
    path('api/nearby-hospitals/', views.api_nearby_hospitals, name='api_nearby_hospitals'),
]
