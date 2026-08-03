import unittest
import os
import tempfile
import sqlite3
import json

# Setup test database path before routes imports it
temp_db_fd, temp_db_path = tempfile.mkstemp()
os.environ['VERCEL'] = ''  # Ensure we are not on Vercel mode in tests

from app import routes
# Override routes DB_PATH to use the temporary file
routes.DB_PATH = temp_db_path
routes.init_db()

from app import create_app

class RoastLabTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['SECRET_KEY'] = 'test_secret_key'

    def setUp(self):
        self.client = self.app.test_client()

        # Clear/reset test database tables
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
            try:
                os.remove(temp_db_path)
            except OSError:
                pass

    def test_indexes_exist(self):
        """Verify that the performance optimization indexes are successfully created."""
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.assertIn('idx_roasts_user_created', indexes)
        self.assertIn('idx_roasts_ip_user_created', indexes)

    def test_rate_limiting_logic_anonymous(self):
        """Verify that rate limiting correctly counts and limits unauthenticated IP requests."""
        # Insert 3 mock roasts for IP '127.0.0.1' with today's timestamp
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        for i in range(3):
            cursor.execute('''
                INSERT INTO roasts (user_id, ip_address, user_input, roast_result)
                VALUES (NULL, '127.0.0.1', ?, ?)
            ''', (f"test input {i}", json.dumps({"headline": "test"})))
        conn.commit()
        conn.close()

        # Try to post a new roast as anonymous
        response = self.client.post('/', data={
            'user_input': 'another attempt',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        })
        self.assertEqual(response.status_code, 200)
        # Check that 'Rate Limit Exceeded' or '3 / 3 Daily Limit' is in the returned content
        html_content = response.data.decode('utf-8')
        self.assertTrue(
            "Rate Limit Exceeded" in html_content or "3 / 3 Daily Limit" in html_content,
            "Daily limit message not found in HTML response"
        )

    def test_rate_limiting_logic_under_limit(self):
        """Verify that a request goes through when under the rate limit."""
        # Insert 2 mock roasts for IP '127.0.0.1' with today's timestamp
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        for i in range(2):
            cursor.execute('''
                INSERT INTO roasts (user_id, ip_address, user_input, roast_result)
                VALUES (NULL, '127.0.0.1', ?, ?)
            ''', (f"test input {i}", json.dumps({"headline": "test"})))
        conn.commit()
        conn.close()

        # Try to post a new roast
        response = self.client.post('/', data={
            'user_input': 'another attempt',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        })
        self.assertEqual(response.status_code, 200)
        html_content = response.data.decode('utf-8')
        self.assertNotIn("Rate Limit Exceeded", html_content)
        self.assertNotIn("3 / 3 Daily Limit", html_content)
