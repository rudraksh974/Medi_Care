from django.contrib import admin
from .models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'gender', 'phone', 'address')
    list_filter = ('gender',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'phone')
