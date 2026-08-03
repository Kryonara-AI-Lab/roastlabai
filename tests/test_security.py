import unittest
from app import create_app

class SecurityHeadersTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_session_secret_key_is_secure(self):
        """Verify that the SECRET_KEY is not the vulnerable hardcoded key."""
        vulnerable_key = 'roastlab_secret_key_change_this_immediately'
        self.assertNotEqual(self.app.config['SECRET_KEY'], vulnerable_key)
        self.assertTrue(len(self.app.config['SECRET_KEY']) >= 32)

    def test_security_headers_on_index(self):
        """Verify that security headers are present on the index route response."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('X-Frame-Options'), 'SAMEORIGIN')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

    def test_security_headers_on_login_and_signup(self):
        """Verify security headers are on login and signup pages too."""
        for path in ['/login', '/signup']:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers.get('X-Frame-Options'), 'SAMEORIGIN')
            self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
            self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

if __name__ == '__main__':
    unittest.main()
