import os
import unittest
import tempfile
from app import create_app

class SecurityTestCase(unittest.TestCase):
    def setUp(self):
        # Use an isolated temp database for testing
        self.db_fd, self.db_path = tempfile.mkstemp()
        os.environ['VERCEL'] = '1'

        # Override DB_PATH in app.routes
        import app.routes
        app.routes.DB_PATH = self.db_path
        app.routes.init_db()

        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_secret_key_configured(self):
        """Verify SECRET_KEY is dynamic and not hardcoded to default placeholder."""
        secret_key = self.app.config.get('SECRET_KEY')
        self.assertIsNotNone(secret_key)
        self.assertNotEqual(secret_key, 'roastlab_secret_key_change_this_immediately')

    def test_security_headers_present(self):
        """Verify essential HTTP security headers are set on responses."""
        response = self.client.get('/')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

if __name__ == '__main__':
    unittest.main()
