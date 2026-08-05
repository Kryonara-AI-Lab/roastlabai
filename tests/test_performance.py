import os
import unittest
import sqlite3
import json
from datetime import datetime, timedelta
from app import create_app
from app.routes import DB_PATH, get_db_connection

class TestPerformanceAndIndex(unittest.TestCase):
    def setUp(self):
        # Configure the app for testing
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = self.app.test_client()

        # Clean the test DB or recreate it
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except OSError:
                pass

        # Trigger DB initialization
        with self.app.app_context():
            from app.routes import init_db
            init_db()

    def tearDown(self):
        # Clean up database after test
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except OSError:
                pass

    def test_composite_indexes_exist(self):
        """Verify that the required high-performance composite indexes are created successfully."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch the list of indexes in the roasts table
        cursor.execute("PRAGMA index_list('roasts')")
        indexes = cursor.fetchall()
        index_names = [index['name'] for index in indexes]

        self.assertIn('idx_roasts_user_created', index_names)
        self.assertIn('idx_roasts_ip_user_created', index_names)

        # Verify columns in the indexes
        cursor.execute("PRAGMA index_info('idx_roasts_user_created')")
        user_idx_info = cursor.fetchall()
        user_idx_cols = [col['name'] for col in user_idx_info]
        self.assertEqual(user_idx_cols, ['user_id', 'created_at'])

        cursor.execute("PRAGMA index_info('idx_roasts_ip_user_created')")
        ip_idx_info = cursor.fetchall()
        ip_idx_cols = [col['name'] for col in ip_idx_info]
        self.assertEqual(ip_idx_cols, ['ip_address', 'user_id', 'created_at'])

        conn.close()

    def test_rate_limiting_with_optimized_queries(self):
        """Test that the new range-based rate limit query counts only today's roasts."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert some older roasts (yesterday)
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (NULL, '127.0.0.1', 'Old Input', '{}', ?)
        ''', (yesterday,))

        # Insert today's roasts (today)
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (NULL, '127.0.0.1', 'Today Input 1', '{}', ?)
        ''', (today,))
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (NULL, '127.0.0.1', 'Today Input 2', '{}', ?)
        ''', (today,))

        conn.commit()
        conn.close()

        # Try to make two more roasts via the client.
        # First one should be allowed (since yesterday's roast doesn't count, and only 2 today)
        response1 = self.client.post('/', data={
            'user_input': 'Third roast today',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        })
        self.assertEqual(response1.status_code, 200)
        self.assertNotIn(b'Hold your horses, founder.', response1.data)

        # The fourth roast should hit the rate-limit (limit of 3 roasts per day)
        response2 = self.client.post('/', data={
            'user_input': 'Fourth roast today',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        })
        self.assertEqual(response2.status_code, 200)
        # Verify the application sets limit_reached to True (which is shown on the UI)
        self.assertIn(b'Hold your horses, founder.', response2.data)

    def test_authenticated_user_rate_limiting(self):
        """Test rate limiting for a registered logged-in user under the optimized query."""
        # Create a user and log in
        response_signup = self.client.post('/signup', data={
            'email': 'testuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response_signup.status_code, 200)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', ('testuser@example.com',))
        user_id = cursor.fetchone()['id']

        # Insert today's roasts for this user
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for i in range(3):
            cursor.execute('''
                INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
                VALUES (?, '127.0.0.1', ?, '{}', ?)
            ''', (user_id, f'Input {i}', today))
        conn.commit()
        conn.close()

        # The user has already consumed 3 roasts today. A new roast should trigger the limit.
        response = self.client.post('/', data={
            'user_input': 'Yet another concept',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Hold your horses, founder.', response.data)

if __name__ == '__main__':
    unittest.main()
