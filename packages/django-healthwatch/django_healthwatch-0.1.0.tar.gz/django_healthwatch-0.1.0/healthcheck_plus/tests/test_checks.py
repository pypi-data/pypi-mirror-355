from django.core.management import call_command
from django.test import TestCase
from io import StringIO
from unittest.mock import patch, MagicMock

class HealthCheckCommandTests(TestCase):
    @patch('healthcheck_plus.management.commands.health_check.registry.get_checks')
    @patch('healthcheck_plus.management.commands.health_check.alert_manager.notify')
    @patch('healthcheck_plus.management.commands.health_check.log_check_result')
    def test_health_check_command_success(self, mock_log, mock_notify, mock_get_checks):
        # إعداد check وهمي بيرجع success
        mock_check = MagicMock()
        mock_check.name = "Database"
        mock_check.status = True
        mock_check.message = "Database OK"
        mock_check.run.return_value = None  # لأن .run() بترجعش حاجة
        mock_get_checks.return_value = [mock_check]

        # الإمساك بالخارج (stdout)
        out = StringIO()
        err = StringIO()

        call_command('health_check', stdout=out, stderr=err)

        self.assertIn("✅ Database: Database OK", out.getvalue())
        self.assertIn("✅ All checks passed.", out.getvalue())
        self.assertEqual(err.getvalue(), "")


