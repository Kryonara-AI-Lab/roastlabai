import os
import sqlite3
import json
import unittest

# Ensure VERCEL is set so routes.py uses isolated DB
os.environ['VERCEL'] = '1'

import app.routes
from app import create_app

class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.test_db_path = '/tmp/roastlab_test.db'
        app.routes.DB_PATH = self.test_db_path
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        app.routes.init_db()

        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test'
        self.client = self.app.test_client()

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_signup_and_login(self):
        # Test signup
        response = self.client.post('/signup', data={
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Logout
        self.client.get('/logout')

        # Test login
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_rate_limit(self):
        # Fill 3 roasts for anonymous IP
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        for i in range(3):
            cursor.execute('''
                INSERT INTO roasts (user_id, ip_address, user_input, roast_result)
                VALUES (NULL, '127.0.0.1', ?, ?)
            ''', (f'test idea {i}', json.dumps({'headline': 'test'})))
        conn.commit()
        conn.close()

        # Submit 4th roast
        response = self.client.post('/', data={
            'user_input': 'Another idea',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rate Limit Exceeded', response.data)

if __name__ == '__main__':
    unittest.main()
