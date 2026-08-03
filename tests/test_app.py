import os
import unittest
import tempfile
import sqlite3
import json
from flask import session

# Override DB_PATH to a temporary file before imports
import app.routes as routes
temp_db_fd, temp_db_path = tempfile.mkstemp()
routes.DB_PATH = temp_db_path

from app import create_app

class RoastLabTestCase(unittest.TestCase):
    def setUp(self):
        # Re-initialize the test database
        routes.init_db()
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = self.app.test_client()

        # Clear database records
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM roasts")
        conn.commit()
        conn.close()

    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
        os.close(temp_db_fd)
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)

    def test_signup_and_login(self):
        # Test basic signup
        response = self.client.post('/signup', data={
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ignite Roast Reactor', response.data)

        # Logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Test login
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ignite Roast Reactor', response.data)

    def test_roast_rate_limit_anonymous(self):
        # Let's perform 3 fallback roasts
        for i in range(3):
            response = self.client.post('/', data={
                'user_input': f'Idea {i}',
                'intensity': 'Savage',
                'personality': 'Tech Bro'
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Substack for ADHD-addled attention spans', response.data)

        # The 4th attempt should hit the daily cap
        response = self.client.post('/', data={
            'user_input': 'Fourth Idea',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"You've processed 3 startup ideas today.", response.data)

    def test_roast_rate_limit_logged_in_user(self):
        # Sign up and log in
        self.client.post('/signup', data={
            'email': 'user@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        # Run 3 roasts
        for i in range(3):
            response = self.client.post('/', data={
                'user_input': f'Logged in Idea {i}',
                'intensity': 'Savage',
                'personality': 'Tech Bro'
            })
            self.assertEqual(response.status_code, 200)

        # 4th roast should be limited
        response = self.client.post('/', data={
            'user_input': 'Logged in Idea 4',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"You've processed 3 startup ideas today.", response.data)

if __name__ == '__main__':
    unittest.main()
