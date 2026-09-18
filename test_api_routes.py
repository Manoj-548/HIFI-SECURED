import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import (
    health_check,
    get_account_holders,
    list_vault_items,
    security_audit_api,
    generate_password_api,
    create_vault_item,
    delete_vault_item,
)
from app.schemas import VaultItemCreate, PasswordGenerateRequest
from app.database import SessionLocal, engine
from app.models import Base, VaultItem

class TestApiDirect(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()
        self.db.query(VaultItem).delete()
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_health_check(self):
        res = health_check()
        self.assertEqual(res["status"], "ok")

    def test_get_account_holders(self):
        res = get_account_holders(db=self.db)
        self.assertTrue(res["success"])
        self.assertGreater(res["total_holders"], 0)

    def test_list_vault_items(self):
        res = list_vault_items(db=self.db)
        self.assertTrue(res["success"])
        self.assertGreaterEqual(res["count"], 6)

    def test_security_audit_api(self):
        res = security_audit_api(db=self.db)
        self.assertTrue(res["success"])
        self.assertIn("average_score", res)

    def test_generate_password_api(self):
        req = PasswordGenerateRequest(length=24, use_uppercase=True, use_digits=True, use_symbols=True)
        res = generate_password_api(req)
        self.assertEqual(len(res.generated_password), 24)

    def test_create_and_delete_vault_item(self):
        payload = VaultItemCreate(
            account_holder_name="Unique Direct API Test Holder",
            service_name="GitHub OAuth App",
            category="Developer API",
            login_email_username="oauth_user@github.org",
            password="OAuthSecretKey_2026!",
            website_url="https://github.com/settings/apps",
            notes="Direct test notes",
            is_favorite=True,
            is_shared_with_specific_user=True
        )
        created = create_vault_item(payload=payload, db=self.db)
        self.assertTrue(created["success"])
        item_id = created["item"]["id"]

        # Filter check
        filtered = list_vault_items(account_holder="Unique Direct API Test Holder", db=self.db)
        self.assertEqual(filtered["count"], 1)

        # Delete check
        del_res = delete_vault_item(item_id=item_id, db=self.db)
        self.assertTrue(del_res["success"])

if __name__ == "__main__":
    unittest.main()
