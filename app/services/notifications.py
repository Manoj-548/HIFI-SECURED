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


notification_service = NotificationService()
