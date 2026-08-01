import os
import unittest
import tempfile
import json
from unittest.mock import patch
from app import create_app
from app.routes import init_db, get_db_connection
import app.routes

class RoastLabTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file
        self.db_fd, self.db_path = tempfile.mkstemp()

        # Patch the DB_PATH in app.routes
        self.patcher = patch('app.routes.DB_PATH', self.db_path)
        self.patcher.start()

        # Initialize the app and test client
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_secret'
        self.client = self.app.test_client()

        # Initialize the test database
        with self.app.app_context():
            init_db()

    def tearDown(self):
        self.patcher.stop()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_index_route_get(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'RoastLab', response.data)

    def test_signup_and_login(self):
        # 1. Sign up a new user
        signup_data = {
            'email': 'tester@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        response = self.client.post('/signup', data=signup_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'SECURED ACCOUNT VAULT: tester@example.com', response.data)

        # Logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertNotIn(b'SECURED ACCOUNT VAULT:', response.data)

        # 2. Login
        login_data = {
            'email': 'tester@example.com',
            'password': 'password123'
        }
        response = self.client.post('/login', data=login_data, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'SECURED ACCOUNT VAULT: tester@example.com', response.data)

    def test_limit_reached_anonymous(self):
        # Anonymous users have a 3-roast limit
        # Perform 3 roasts
        for i in range(3):
            response = self.client.post('/', data={
                'user_input': f'Idea number {i}',
                'intensity': 'Savage',
                'personality': 'Tech Bro'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(b'Rate Limit Exceeded', response.data)

        # 4th roast should trigger rate limit
        response = self.client.post('/', data={
            'user_input': 'Idea number 4',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rate Limit Exceeded', response.data)

    def test_save_and_delete_verdict(self):
        # Log in first
        signup_data = {
            'email': 'saver@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        self.client.post('/signup', data=signup_data, follow_redirects=True)

        # Save verdict
        verdict_payload = {
            'user_input': 'My awesome startup',
            'roast_result': {
                'headline': 'Dreadful project',
                'score': 10,
                'roast_bullets': ['Bad', 'Very bad'],
                'brutal_truth': 'Truth hurts',
                'worth_saving': 'Nothing',
                'eats_lunch': 'Everyone',
                'one_move': 'Give up'
            }
        }
        response = self.client.post('/save_verdict',
                                    data=json.dumps(verdict_payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.data)
        self.assertTrue(res_json.get('success'))

        # Check that it appears in history
        response = self.client.get('/')
        self.assertIn(b'Dreadful project', response.data)

        # Delete verdict
        # Get verdict ID from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM roasts WHERE user_input = ?', ('My awesome startup',))
        verdict_id = cursor.fetchone()[0]
        conn.close()

        response = self.client.post(f'/delete_verdict/{verdict_id}')
        self.assertEqual(response.status_code, 200)
        res_json = json.loads(response.data)
        self.assertTrue(res_json.get('success'))

        # Verify it's gone from history
        response = self.client.get('/')
        self.assertNotIn(b'Dreadful project', response.data)

if __name__ == '__main__':
    unittest.main()
