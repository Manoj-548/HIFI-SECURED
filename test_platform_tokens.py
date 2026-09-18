import unittest
import json
from fastapi.testclient import TestClient
from app.main import app

class TestPlatformTokensAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_01_list_platform_tokens(self):
        res = self.client.get("/api/tokens/platform-tokens")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["count"], 6)
        platforms = [t["platform_name"] for t in data["platform_tokens"]]
        self.assertIn("GitHub Developer API", platforms)
        self.assertIn("Google Cloud Platform", platforms)
        self.assertIn("AWS Enterprise Infrastructure", platforms)

    def test_02_create_platform_token(self):
        payload = {
            "platform_name": "Slack Corporate Desk",
            "token_label": "Slack DevOps Alerts Webhook",
            "scopes": "incoming-webhook, chat:write",
            "expiry_minutes": 10080
        }
        res = self.client.post("/api/tokens/platform-tokens", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["platform_token"]["platform_name"], "Slack Corporate Desk")
        self.assertTrue(data["platform_token"]["zero_knowledge_hash"].startswith("TK-SLA"))
        token_id = data["platform_token"]["id"]

        # Revoke created token
        revoke_res = self.client.post(f"/api/tokens/platform-tokens/{token_id}/revoke")
        self.assertEqual(revoke_res.status_code, 200)
        self.assertTrue(revoke_res.json()["success"])

    def test_03_trigger_platform_alert(self):
        res = self.client.get("/api/tokens/platform-tokens")
        token_id = res.json()["platform_tokens"][0]["id"]

        alert_res = self.client.post(f"/api/tokens/platform-tokens/{token_id}/trigger-alert")
        self.assertEqual(alert_res.status_code, 200)
        self.assertTrue(alert_res.json()["success"])
        self.assertIn("Multi-Channel Intentionality Alert", alert_res.json()["message"])

if __name__ == '__main__':
    unittest.main()
