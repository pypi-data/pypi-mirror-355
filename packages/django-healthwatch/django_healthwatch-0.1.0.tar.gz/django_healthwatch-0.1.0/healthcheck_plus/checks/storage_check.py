import os
from django.core.files.storage import default_storage
from .base import BaseCheck


class StorageCheck(BaseCheck):
    name = "storage"
    description = "Check media storage"

    def run(self):
        test_path = "healthcheck_plus_test.txt"

        try: 
            with default_storage.open(test_path, 'w') as f:
                f.write("OK")
            with default_storage.open(test_path, 'r') as f:
                content = f.read()
            default_storage.delete(test_path)

            if content == "OK":
                self.status = True
                self.message = "Storage is working ok ✅."
            else:
                self.status = False
                self.message = "Storage content mismatch ❌"
        except Exception as e:
            self.status = False
            self.message = f"Storage check failed ❌: {str(e)}"