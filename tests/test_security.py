import unittest
import os
from app import create_app

class SecurityConfigTestCase(unittest.TestCase):
    def setUp(self):
        # We can clear environment variables to test default/fallback behavior
        self.old_secret = os.environ.get('SECRET_KEY')
        self.old_flask_secret = os.environ.get('FLASK_SECRET_KEY')
        if 'SECRET_KEY' in os.environ:
            del os.environ['SECRET_KEY']
        if 'FLASK_SECRET_KEY' in os.environ:
            del os.environ['FLASK_SECRET_KEY']

        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def tearDown(self):
        if self.old_secret is not None:
            os.environ['SECRET_KEY'] = self.old_secret
        if self.old_flask_secret is not None:
            os.environ['FLASK_SECRET_KEY'] = self.old_flask_secret

    def test_session_secret_key_fallback_is_secure(self):
        """Verify that the SECRET_KEY is not the vulnerable hardcoded key."""
        vulnerable_key = 'roastlab_secret_key_change_this_immediately'
        self.assertNotEqual(self.app.config['SECRET_KEY'], vulnerable_key)
        self.assertTrue(len(self.app.config['SECRET_KEY']) >= 32)

    def test_session_secret_key_from_env(self):
        """Verify that the SECRET_KEY is loaded from environment if provided."""
        os.environ['SECRET_KEY'] = 'test_custom_env_secret_key_12345'
        app_custom = create_app()
        self.assertEqual(app_custom.config['SECRET_KEY'], 'test_custom_env_secret_key_12345')

    def test_session_cookie_security_flags(self):
        """Verify that session cookies are configured defensively."""
        self.assertTrue(self.app.config['SESSION_COOKIE_HTTPONLY'])
        self.assertEqual(self.app.config['SESSION_COOKIE_SAMESITE'], 'Lax')

    def test_security_headers_on_index(self):
        """Verify that defense-in-depth security headers are present on the index response."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

    def test_security_headers_on_auth_pages(self):
        """Verify defense-in-depth security headers are present on other pages (e.g. login/signup)."""
        for path in ['/login', '/signup']:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
            self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
            self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

if __name__ == '__main__':
    unittest.main()
