from typing import Any


class NotificationService:
    def __init__(self):
        self.enabled = False

    async def send_email_alert(self, email: str, message: str) -> bool:
        return True

    async def send_whatsapp_alert(self, phone: str, message: str) -> bool:
        return True

    async def queue_notification(self, user_id: Any, channel: str, message: str, notification_type: str = "security") -> None:
        return None

    async def send_breach_alert(self, email: str, phone: str, incident: str) -> dict:
        return {
            "email": True,
            "whatsapp": True,
            "incident": incident,
            "recipient_email": email,
            "recipient_phone": phone,
        }


notification_service = NotificationService()
