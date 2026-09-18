import unittest
import json
import urllib.request

BASE_URL = "http://127.0.0.1:8080"

class TestHifiSecuredParityIntegration(unittest.TestCase):

    def test_01_health_endpoint(self):
        req = urllib.request.Request(f"{BASE_URL}/health")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertEqual(data["status"], "ok")
            self.assertEqual(data["plan_price_inr"], 200)

    def test_02_parity_repos_endpoint(self):
        req = urllib.request.Request(f"{BASE_URL}/api/parity/repos")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertTrue(data["success"])
            self.assertEqual(len(data["repos"]), 4)
            ports = [r["port"] for r in data["repos"]]
            self.assertIn(3000, ports)
            self.assertIn(8000, ports)
            self.assertIn(8080, ports)
            self.assertIn(5000, ports)

    def test_03_lag_analysis_endpoint(self):
        req = urllib.request.Request(f"{BASE_URL}/api/parity/lag-analysis")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertTrue(data["success"])
            self.assertIn("comparisons", data)

    def test_04_blackbox_case_study_endpoint(self):
        req = urllib.request.Request(f"{BASE_URL}/api/blackbox/case-study")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertTrue(data["success"])
            self.assertEqual(data["active_hifi_protection_status"], "100% PROTECTED & ISOLATED")
            self.assertGreaterEqual(len(data["live_suggestions"]), 4)

    def test_05_groups_endpoints(self):
        req = urllib.request.Request(f"{BASE_URL}/api/groups")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertTrue(data["success"])

        create_payload = json.dumps({"name": "Integration Test Group"}).encode('utf-8')
        create_req = urllib.request.Request(f"{BASE_URL}/api/groups/create", data=create_payload, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(create_req) as resp:
            self.assertEqual(resp.status, 200)
            create_data = json.loads(resp.read().decode())
            grp_code = create_data["group"]["code"]

        join_payload = json.dumps({"code": grp_code, "role": "PR Contributor"}).encode('utf-8')
        join_req = urllib.request.Request(f"{BASE_URL}/api/groups/join", data=join_payload, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(join_req) as resp:
            self.assertEqual(resp.status, 200)
            join_data = json.loads(resp.read().decode())
            self.assertTrue(join_data["success"])

if __name__ == "__main__":
    unittest.main()
