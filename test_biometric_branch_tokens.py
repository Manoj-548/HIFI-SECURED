import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestBiometricAndBranchTokensAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_01_verify_biometric(self):
        res = self.client.post("/api/security/biometric/verify", json={
            "credential_id": "passkey-faceid-99",
            "biometric_type": "face_id",
            "user_email": "demo@example.com"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["authenticated"])
        self.assertTrue(data["fallback_2fa_available"])
        self.assertIn("FACE ID", data["auth_method"])

    def test_02_list_git_branches(self):
        res = self.client.get("/api/git/branches")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["total_branches"], 5)
        b_names = [b["branch_name"] for b in data["branches"]]
        self.assertIn("main", b_names)
        self.assertIn("feature/invisible-token-cipher", b_names)
        self.assertIn("feature/biometric-gate", b_names)
        self.assertIn("staging", b_names)

    def test_03_rotate_branch_token(self):
        res = self.client.post("/api/git/branches/rotate-token", json={
            "branch_name": "feature/invisible-token-cipher",
            "rotate_recursively_team": True
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["branch_name"], "feature/invisible-token-cipher")
        self.assertEqual(data["rotation_status"], "ROTATED & TEAM SYNCED")
        self.assertIn("Manoj-548 / HIFI-SECURED", data["team_remotes_synced"])

    def test_04_approve_pr_biometric(self):
        res = self.client.post("/api/pr/biometric-approve", json={
            "pr_id": "PR-101",
            "reviewer_email": "demo@example.com",
            "auth_method": "biometric"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["status"], "APPROVED & MERGED")
        self.assertTrue(data["single_source_of_truth_sync"])

    def test_05_bootstrap_failures(self):
        res = self.client.get("/api/security/bootstrap-failures")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["total_noted_failures"], 3)
        self.assertIn("PROVEN SAFE", data["zero_leak_status"])

        f_id = data["bootstrap_logs"][0]["id"]
        resolve_res = self.client.post(f"/api/security/bootstrap-failures/{f_id}/resolve")
        self.assertEqual(resolve_res.status_code, 200)
        self.assertTrue(resolve_res.json()["success"])

if __name__ == '__main__':
    unittest.main()

