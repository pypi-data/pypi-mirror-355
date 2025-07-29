from django.core.cache import cache
from .base import BaseCheck


class CacheCheck(BaseCheck):
    name = "Cache Check"
    description = "Check cache write/read"

    def run(self):
        try:
            cache.set("healthcheck_plus_test", "OK", timeout=5)
            value = cache.get("healthcheck_plus_test")
            if value == "OK":
                self.status = True
                self.message = "Cache is working properly ✅."
            else:
                self.status = False
                self.message = "Cache mismatch ❌"
        except Exception as e:
            self.status = False
            self.message = f"Cache check failed ❌: {str(e)}"
            