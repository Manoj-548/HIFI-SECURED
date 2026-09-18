import unittest
import os
import sys

# Ensure project directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.security import encrypt_credential, decrypt_credential, calculate_password_score, generate_secure_password
from app.database import engine, SessionLocal
from app.models import Base, VaultItem
from app.schemas import VaultItemCreate, PasswordGenerateRequest

class TestVaultEngine(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_encryption_decryption(self):
        original = "SecretMasterPassword_2026!"
        encrypted = encrypt_credential(original)
        self.assertNotEqual(original, encrypted)
        decrypted = decrypt_credential(encrypted)
        self.assertEqual(original, decrypted)

    def test_password_score(self):
        score_weak = calculate_password_score("12345")
        score_strong = calculate_password_score("P@ssw0rd_Super_Strong_2026!")
        self.assertLess(score_weak, 50)
        self.assertGreaterEqual(score_strong, 80)

    def test_secure_password_generator(self):
        pwd = generate_secure_password(length=20, use_uppercase=True, use_digits=True, use_symbols=True)
        self.assertEqual(len(pwd), 20)
        self.assertTrue(any(c.isupper() for c in pwd))
        self.assertTrue(any(c.isdigit() for c in pwd))

    def test_vault_crud(self):
        test_item = VaultItem(
            account_holder_name="Manoj Test Holder",
            service_name="GitHub Unit Test",
            category="Developer API",
            login_email_username="test_user@github.com",
            encrypted_password=encrypt_credential("UnitTestPass_9988!"),
            website_url="https://github.com",
            notes_encrypted=encrypt_credential("Unit test secret notes"),
            security_score=85,
            is_favorite=True
        )
        self.db.add(test_item)
        self.db.commit()
        self.db.refresh(test_item)

        saved = self.db.query(VaultItem).filter(VaultItem.id == test_item.id).first()
        self.assertIsNotNone(saved)
        self.assertEqual(saved.account_holder_name, "Manoj Test Holder")
        self.assertEqual(decrypt_credential(saved.encrypted_password), "UnitTestPass_9988!")

        # Clean up
        self.db.delete(saved)
        self.db.commit()

if __name__ == "__main__":
    unittest.main()
