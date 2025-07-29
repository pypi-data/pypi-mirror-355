from django.db import models

class HealthCheckLog(models.Model):
    name = models.CharField(max_length=100)
    status = models.BooleanField()
    message = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp} - {self.name} - {'✅' if self.status else '❌'}"
