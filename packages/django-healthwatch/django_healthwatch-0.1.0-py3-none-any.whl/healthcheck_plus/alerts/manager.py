class HealthAlertManager:
    def __init__(self):
        self.alerters = []
        self.last_status = {}  

    def register(self, alerter):
        self.alerters.append(alerter)

    def notify(self, check):
        if check.name in self.last_status and self.last_status[check.name] == check.status:
            return 

        self.last_status[check.name] = check.status

        for alerter in self.alerters:
            alerter.send(check.name, check.status, check.message)

alert_manager = HealthAlertManager()
