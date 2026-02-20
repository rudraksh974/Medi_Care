from django.urls import path
from . import views

urlpatterns = [
    path('',views.home,name='home'),
    # path("test-email/", views.test_email), // ONLY FOR TESTING
    path('predict/',views.predict_disease,name='predict_disease'),
]