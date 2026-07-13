from django.contrib import admin
from django.utils.html import format_html
from .models import Doctor

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'registration_number', 'state_council', 'registration_year', 'verification_document_link', 'is_verified', 'available', 'location')
    list_filter = ('is_verified', 'specialization', 'available')
    list_editable = ('is_verified', 'available')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'registration_number')
    readonly_fields = ('nmr_verification_link', 'verification_document_link')

    def nmr_verification_link(self, obj):
        if obj.registration_number:
            url = "https://www.nmc.org.in/information-desk/indian-medical-register/"
            return format_html(
                '<a href="{}" target="_blank" style="font-weight: bold; color: #2563eb; text-decoration: underline;">Verify on NMC Portal (Reg No: {})</a>',
                url,
                obj.registration_number
            )
        return "No Registration Number provided."
    nmr_verification_link.short_description = "NMC Medical Register"

    def verification_document_link(self, obj):
        if obj.verification_document:
            return format_html(
                '<a href="{}" target="_blank" style="font-weight: bold; color: #10b981; text-decoration: underline;">📄 View Document</a>',
                obj.verification_document.url
            )
        return "No document uploaded."
    verification_document_link.short_description = "Verification Document"
