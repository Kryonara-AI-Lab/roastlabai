import unittest
import sqlite3
import os
import json

# Set VERCEL environment variable before importing routes to prevent top-level module load from modifying app/roastlab.db
os.environ['VERCEL'] = '1'

import app.routes
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), 'test_roastlab_temp.db')
app.routes.DB_PATH = TEST_DB_PATH

from app import create_app
from app.routes import init_db

class TestDatabaseOptimization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize test database
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        init_db()

    @classmethod
    def tearDownClass(cls):
        # Clean up test database file
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except OSError:
                pass

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Clear existing tables inside the temporary test database
        conn = sqlite3.connect(TEST_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM roasts")
        cursor.execute("DELETE FROM users")
        conn.commit()
        conn.close()

    def test_query_plan_optimization(self):
        """Verifies that the database uses covering indexes for rate-limit checks."""
        conn = sqlite3.connect(TEST_DB_PATH)
        cursor = conn.cursor()

        # Check logged-in user count plan
        cursor.execute("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM roasts WHERE user_id = 1 AND created_at >= date('now')")
        user_plan = cursor.fetchall()
        print("\n[TEST] User Query Plan:", user_plan)
        self.assertTrue(any("idx_roasts_user_created" in r[3] for r in user_plan), "Index idx_roasts_user_created should be utilized")

        # Check anonymous IP count plan
        cursor.execute("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM roasts WHERE ip_address = '127.0.0.1' AND user_id IS NULL AND created_at >= date('now')")
        ip_plan = cursor.fetchall()
        print("[TEST] IP Query Plan:", ip_plan)
        self.assertTrue(any("idx_roasts_ip_user_created" in r[3] for r in ip_plan), "Index idx_roasts_ip_user_created should be utilized")

        conn.close()

    def test_anonymous_rate_limiting(self):
        """Verifies that the rate-limiting count of 3 per day is enforced correctly."""
        # 1. Post 3 roasts as anonymous user
        for i in range(3):
            response = self.client.post('/', data={
                'user_input': f'Startup Idea Number {i}',
                'intensity': 'Savage',
                'personality': 'Tech Bro'
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Substack for ADHD-addled attention spans', response.data, "Should return successful fallback roast result")

        # 2. 4th post should trigger the rate limit reached block
        response = self.client.post('/', data={
            'user_input': 'Startup Idea Number 4',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rate Limit Exceeded', response.data, "4th request should trigger daily rate limit")

    def test_logged_in_rate_limiting(self):
        """Verifies rate-limiting for a logged-in user is distinct and enforced."""
        # 1. Sign up a new user
        signup_resp = self.client.post('/signup', data={
            'email': 'test@test.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(signup_resp.status_code, 200)

        # 2. Post 3 roasts
        for i in range(3):
            response = self.client.post('/', data={
                'user_input': f'Logged-in Idea Number {i}',
                'intensity': 'Savage',
                'personality': 'Tech Bro'
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Substack for ADHD-addled attention spans', response.data)

        # 3. 4th post should exceed the limit
        response = self.client.post('/', data={
            'user_input': 'Logged-in Idea Number 4',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rate Limit Exceeded', response.data)

if __name__ == '__main__':
    unittest.main()
