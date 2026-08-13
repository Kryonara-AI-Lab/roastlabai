import os
import unittest
# Set VERCEL to bypass local DB path during imports if needed
os.environ['VERCEL'] = '1'

from app import create_app

class TestSecurityConfigurations(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_secret_key_is_dynamic(self):
        """Verify that SECRET_KEY is not the hardcoded vulnerable default."""
        vuln_default = 'roastlab_secret_key_change_this_immediately'
        self.assertNotEqual(self.app.config.get('SECRET_KEY'), vuln_default)
        self.assertIsNotNone(self.app.config.get('SECRET_KEY'))

    def test_security_headers_present(self):
        """Verify that global security headers are correctly applied via @bp.after_request."""
        response = self.client.get('/')

        self.assertEqual(response.headers.get('X-Frame-Options'), 'SAMEORIGIN')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

if __name__ == '__main__':
    unittest.main()
