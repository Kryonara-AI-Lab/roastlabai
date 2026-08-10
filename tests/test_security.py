import unittest
import os
from app import create_app

class SecurityTestCase(unittest.TestCase):
    def setUp(self):
        # Set up a test application with a unique configuration
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_security_headers(self):
        """Test that global security headers are correctly appended to all responses."""
        response = self.client.get('/')
        self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(response.headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')

    def test_dynamic_secret_key(self):
        """Test that SECRET_KEY is set securely and dynamically."""
        # Ensure secret key is initialized and is not the old static placeholder
        secret_key = self.app.config.get('SECRET_KEY')
        self.assertIsNotNone(secret_key)
        self.assertNotEqual(secret_key, 'roastlab_secret_key_change_this_immediately')

        # Test that SECRET_KEY will prioritize environment variable if available
        os.environ['SECRET_KEY'] = 'super-secret-override-value'
        override_app = create_app()
        self.assertEqual(override_app.config.get('SECRET_KEY'), 'super-secret-override-value')
        del os.environ['SECRET_KEY']

if __name__ == '__main__':
    unittest.main()
