from django.core.management.base import BaseCommand
from healthcheck_plus.registry import registry
from healthcheck_plus.alerts.manager import alert_manager
from healthcheck_plus.utils import log_check_result

class Command(BaseCommand):
    help = 'Run all health checks'

    def handle(self, *args, **options):
        all_ok = True
        for check in registry.get_checks():
            check.run()
            alert_manager.notify(check)
            log_check_result(check.name, check.status, check.message)

            icon = "✅" if check.status else "❌"
            self.stdout.write(f"{icon} {check.name}: {check.message}")
            if not check.status:
                all_ok = False

        if not all_ok:
            self.stderr.write("❌ One or more checks failed.")
            exit(1)
        else:
            self.stdout.write("✅ All checks passed.")
