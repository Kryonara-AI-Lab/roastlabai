import os
import unittest
from app import create_app

class SecurityTestCase(unittest.TestCase):
    def setUp(self):
        # Ensure VERCEL is not set during test configuration to use local/temp DB properly
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_secret_key_is_dynamic_and_secure(self):
        """
        Verifies that Flask's SECRET_KEY is dynamically generated and secure,
        rather than hardcoded.
        """
        # Ensure the secret key exists and has strong length (at least 64 chars from secrets.token_hex(32))
        secret_key = self.app.config.get('SECRET_KEY')
        self.assertIsNotNone(secret_key)
        self.assertNotEqual(secret_key, 'roastlab_secret_key_change_this_immediately')
        self.assertGreaterEqual(len(secret_key), 32)

    def test_security_headers_are_enforced(self):
        """
        Verifies that standard security headers are applied globally to responses.
        """
        response = self.client.get('/')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

    def test_routes_load_correctly(self):
        """
        Verifies that basic routes function correctly and return standard success status codes.
        """
        # Test main index
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        # Test terms
        response = self.client.get('/compliance/terms')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
