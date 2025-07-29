

class HealthCheckRegistry:
    """
    A registry for health check classes.
    """

    def __init__(self):
        self._registry = {}

    def register(self, check_class):
        if not check_class.name:
            raise ValueError("Check class must have a 'name' attribute")
        self._registry[check_class.name] = check_class()

    def get_checks(self):
        return self._registry.values()


registry = HealthCheckRegistry()
