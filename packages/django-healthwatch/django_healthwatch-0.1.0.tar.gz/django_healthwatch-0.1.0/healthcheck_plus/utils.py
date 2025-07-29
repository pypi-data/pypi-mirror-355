from django.conf import settings
from .models import HealthCheckLog

def log_check_result(name, status, message):
    HealthCheckLog.objects.create(name=name, status=status, message=message)

    limit = getattr(settings, 'HEALTHCHECK_LOG_LIMIT', 100)
    excess = HealthCheckLog.objects.filter(name=name).order_by('-timestamp')[limit:]
    if excess.exists():
        excess.delete()
