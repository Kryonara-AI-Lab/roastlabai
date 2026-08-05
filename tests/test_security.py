import unittest
import os
from app import create_app

class SecurityTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_security_headers(self):
        """Verify that security headers are enforced globally via bp.after_request"""
        response = self.client.get('/')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'no-referrer-when-downgrade')

    def test_secure_session_key(self):
        """Verify that the SECRET_KEY is set securely and dynamically"""
        # Ensure SECRET_KEY is not the vulnerable hardcoded fallback
        self.assertNotEqual(self.app.config['SECRET_KEY'], 'roastlab_secret_key_change_this_immediately')
        self.assertTrue(len(self.app.config['SECRET_KEY']) >= 16)

if __name__ == '__main__':
    unittest.main()
