from django.core.mail import send_mail
from .base import BaseAlerter

class EmailAlerter(BaseAlerter):
    def send(self, check_name, status, message):
        subject = f"[HealthCheck] {check_name} failed!" if not status else f"[HealthCheck] {check_name} OK"
        body = message
        send_mail(
            subject,
            body,
            'motazfawzy73@gmail.com',
            ['motazfawzy73@gmail.com'],
            fail_silently=True
        )
