import os
import unittest
from app import create_app

class SecurityTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_security_headers_enforced(self):
        """Assert that security headers are returned on all routes."""
        response = self.client.get('/')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

    def test_session_cookie_settings_secure(self):
        """Assert that session cookie configuration has HTTPOnly and Samesite=Lax."""
        self.assertTrue(self.app.config['SESSION_COOKIE_HTTPONLY'])
        self.assertEqual(self.app.config['SESSION_COOKIE_SAMESITE'], 'Lax')

    def test_dynamic_secret_key(self):
        """Assert that SECRET_KEY is not the hardcoded default and is sufficiently complex."""
        self.assertIsNotNone(self.app.config['SECRET_KEY'])
        self.assertNotEqual(self.app.config['SECRET_KEY'], 'roastlab_secret_key_change_this_immediately')
        self.assertGreater(len(self.app.config['SECRET_KEY']), 16)

if __name__ == '__main__':
    unittest.main()
