from .base import BaseAlerter

class SMSAlerter(BaseAlerter):
    def send(self, check_name, status, message):
        print(f"📲 SMS Alert - {check_name}: {message}")
