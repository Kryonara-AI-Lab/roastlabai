import os
import unittest

# Set environment variable VERCEL to isolate test DB if needed
os.environ['VERCEL'] = '1'

from app import create_app

class SecurityTestCase(unittest.TestCase):
    def test_secret_key_not_default_or_hardcoded(self):
        """Test that Flask SECRET_KEY is dynamically configured and not set to the insecure hardcoded key."""
        app = create_app()
        secret_key = app.config.get('SECRET_KEY')
        self.assertIsNotNone(secret_key)
        self.assertNotEqual(secret_key, 'roastlab_secret_key_change_this_immediately')
        self.assertTrue(len(secret_key) >= 16)

    def test_secret_key_environment_override(self):
        """Test that SECRET_KEY respects environment variable when provided."""
        custom_key = 'custom_env_secret_key_for_testing_12345'
        os.environ['SECRET_KEY'] = custom_key
        try:
            app = create_app()
            self.assertEqual(app.config.get('SECRET_KEY'), custom_key)
        finally:
            del os.environ['SECRET_KEY']

if __name__ == '__main__':
    unittest.main()
