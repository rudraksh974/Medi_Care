from django.db import models
from django.conf import settings
import json

class PredictionRecord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    symptoms = models.TextField()
    predicted_disease = models.CharField(max_length=100)
    confidence = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    precautions = models.TextField(blank=True, null=True)  # Store as JSON string or text
    specialist = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def precautions_list(self):
        try:
            return json.loads(self.precautions)
        except Exception:
            if self.precautions:
                return [p.strip() for p in self.precautions.split(",") if p.strip()]
            return []

    def __str__(self):
        return f"{self.user} - {self.predicted_disease}"
