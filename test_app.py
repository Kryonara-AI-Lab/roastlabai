import unittest
import os
from app import create_app

class SecurityTestCase(unittest.TestCase):
    def setUp(self):
        # Force a secret key for testing context
        os.environ['SECRET_KEY'] = 'testsecretkey12345'
        self.app = create_app()
        self.client = self.app.test_client()

    def test_security_headers(self):
        response = self.client.get('/')
        # Verify the security headers we added are present and correct
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

    def test_pages_load(self):
        # Ensure standard pages load successfully without regression
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/signup')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
