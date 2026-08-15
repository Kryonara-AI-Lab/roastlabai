import unittest
import os
from app import create_app

class TestSecurityConfig(unittest.TestCase):
    def test_secret_key_from_env(self):
        os.environ['SECRET_KEY'] = 'test_secret_key_12345'
        app = create_app()
        self.assertEqual(app.config['SECRET_KEY'], 'test_secret_key_12345')
        del os.environ['SECRET_KEY']

    def test_secret_key_fallback_randomness(self):
        if 'SECRET_KEY' in os.environ:
            del os.environ['SECRET_KEY']
        app1 = create_app()
        app2 = create_app()
        self.assertNotEqual(app1.config['SECRET_KEY'], 'roastlab_secret_key_change_this_immediately')
        self.assertNotEqual(app1.config['SECRET_KEY'], app2.config['SECRET_KEY'])
        self.assertEqual(len(app1.config['SECRET_KEY']), 64)

if __name__ == '__main__':
    unittest.main()
