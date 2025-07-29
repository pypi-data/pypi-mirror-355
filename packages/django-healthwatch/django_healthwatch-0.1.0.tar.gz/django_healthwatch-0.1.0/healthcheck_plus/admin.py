from django.contrib import admin
from .models import HealthCheckLog

@admin.register(HealthCheckLog)
class HealthCheckLogAdmin(admin.ModelAdmin):
    list_display = ('name', 'status_icon', 'message_short', 'timestamp')
    list_filter = ('name', 'status')
    search_fields = ('name', 'message')
    ordering = ('-timestamp',)

    def status_icon(self, obj: HealthCheckLog) -> str:
        return "✅" if obj.status else "❌"
    status_icon.short_description = 'Status'

    def message_short(self, obj: HealthCheckLog) -> str:
        return obj.message[:60] + "..." if obj.message and len(obj.message) > 60 else obj.message
    
    message_short.short_description = 'Message'
