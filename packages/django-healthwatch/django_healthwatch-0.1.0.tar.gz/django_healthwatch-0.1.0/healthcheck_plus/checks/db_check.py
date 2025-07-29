from django.db import connections
from .base import BaseCheck, CheckResult

class DatabaseCheck(BaseCheck):
    name = "Database Check"
    description = "Checks the connection to the database."

    def run(self):
        try:
            connection = connections['default']
            connection.ensure_connection()
            return CheckResult(success=True, message="Database connection is ok ✅.")
        except Exception as e:
            print("❌ DB Error:", e)  # ✅ اطبع الخطأ

            return CheckResult(success=False, message=f"Database connection failed ❌: {str(e)}")
