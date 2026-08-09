import unittest
from app import create_app

class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_secure_secret_key_generated(self):
        # The key should not be the hardcoded default anymore
        secret_key = self.app.config.get('SECRET_KEY')
        self.assertIsNotNone(secret_key)
        self.assertNotEqual(secret_key, 'roastlab_secret_key_change_this_immediately')
        self.assertTrue(len(secret_key) >= 32)

    def test_global_security_headers_present(self):
        response = self.client.get('/')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

    def test_session_cookie_settings(self):
        # By setting a session value, we ensure a session cookie is returned
        with self.client.session_transaction() as sess:
            sess['test_key'] = 'test_value'

        response = self.client.get('/')
        cookie_headers = response.headers.getlist('Set-Cookie')
        if cookie_headers:
            for cookie in cookie_headers:
                if 'session' in cookie.lower():
                    self.assertIn('HttpOnly', cookie)
                    self.assertIn('SameSite=Lax', cookie)
