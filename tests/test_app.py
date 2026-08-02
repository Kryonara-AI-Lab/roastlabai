import unittest
import os
import sqlite3
import json
from app import create_app
from app.routes import DB_PATH, get_db_connection

class RoastLabTestCase(unittest.TestCase):
    def setUp(self):
        # Override the database path to use a test database
        self.test_db_path = '/tmp/roastlab_test.db'
        # Patch the DB_PATH inside routes module
        import app.routes
        app.routes.DB_PATH = self.test_db_path

        # Remove any leftover test DB
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        # Initialize DB
        with self.app.app_context():
            app.routes.init_db()

    def tearDown(self):
        # Clean up database
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except OSError:
                pass

    def test_signup_login_logout(self):
        # 1. Test signup
        response = self.client.post('/signup', data={
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'LOGOUT', response.data) # Logged in automatically

        # 2. Test logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'LOGOUT', response.data)

        # 3. Test login
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'LOGOUT', response.data)

    def test_guest_rate_limiting(self):
        # Generate 3 roasts as guest user
        for i in range(3):
            response = self.client.post('/', data={
                'user_input': f'My amazing startup idea {i}',
                'intensity': 'Savage',
                'personality': 'Tech Bro'
            })
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(b"You've processed 3 startup ideas today", response.data)

        # The 4th roast should trigger the limit
        response = self.client.post('/', data={
            'user_input': 'Another idea that should be blocked',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"You've processed 3 startup ideas today", response.data)

    def test_user_rate_limiting(self):
        # 1. Signup and log in
        self.client.post('/signup', data={
            'email': 'user@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        # 2. Generate 3 roasts as logged-in user
        for i in range(3):
            response = self.client.post('/', data={
                'user_input': f'User startup idea {i}',
                'intensity': 'Savage',
                'personality': 'Tech Bro'
            })
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(b"You've processed 3 startup ideas today", response.data)

        # 3. The 4th roast should trigger the limit
        response = self.client.post('/', data={
            'user_input': 'User fourth idea that should be blocked',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"You've processed 3 startup ideas today", response.data)

    def test_history_and_verdict_deletion(self):
        # 1. Signup and log in
        self.client.post('/signup', data={
            'email': 'history_user@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        # 2. Add a roast
        self.client.post('/', data={
            'user_input': 'Save me, Obi-Wan',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        })

        # 3. Retrieve history and assert correctness
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Substack for ADHD-addled', response.data)

        # 4. Get the roast ID from test DB
        conn = sqlite3.connect(self.test_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM roasts')
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        roast_id = row['id']
        conn.close()

        # 5. Delete the roast via POST endpoint
        response = self.client.post(f'/delete_verdict/{roast_id}')
        self.assertEqual(response.status_code, 200)
        res_data = json.loads(response.data)
        self.assertTrue(res_data['success'])

        # 6. Verify history is empty
        response = self.client.get('/')
        self.assertNotIn(b'Substack for ADHD-addled', response.data)

    def test_pages(self):
        pages = [
            '/privacy.html', '/terms.html', '/DCL.html', '/Model.html',
            '/company/manifesto', '/company/pricing', '/company/protocol', '/company/logs'
        ]
        for page in pages:
            response = self.client.get(page)
            self.assertEqual(response.status_code, 200, f"Page {page} failed to load.")

if __name__ == '__main__':
    unittest.main()
