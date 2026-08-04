import os
import unittest
import sqlite3
import json
from datetime import datetime, timedelta
from app import create_app
from app.routes import DB_PATH, get_db_connection, init_db

class RoastLabTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = self.app.test_client()

        # Connect to the DB and make sure we can inspect it
        # Note: routes.py automatically calls init_db() on load,
        # which creates the DB at DB_PATH.
        self.db_conn = get_db_connection()

    def tearDown(self):
        self.db_conn.close()

    def test_database_indexes_exist(self):
        """Test that the optimized composite indexes exist in the database."""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row['name'] for row in cursor.fetchall()]

        self.assertIn('idx_roasts_user_created', indexes, "idx_roasts_user_created index is missing!")
        self.assertIn('idx_roasts_ip_user_created', indexes, "idx_roasts_ip_user_created index is missing!")

    def test_rate_limiting_logic_and_queries(self):
        """Test that range-based queries correctly identify roasts created today."""
        cursor = self.db_conn.cursor()

        # Clear existing roasts for clean slate
        cursor.execute("DELETE FROM roasts")
        self.db_conn.commit()

        # Insert some dummy roasts:
        # 1. One from yesterday (should not count)
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (1, '127.0.0.1', 'yesterday input', '{}', yesterday))

        # 2. Two from today (should count)
        today_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (1, '127.0.0.1', 'today input 1', '{}', today_now))
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (1, '127.0.0.1', 'today input 2', '{}', today_now))
        self.db_conn.commit()

        # Run the refactored range-based query for logged-in user (user_id = 1)
        cursor.execute('''
            SELECT COUNT(*) FROM roasts
            WHERE user_id = ? AND created_at >= date('now')
        ''', (1,))
        count_user = cursor.fetchone()[0]
        self.assertEqual(count_user, 2, "Range-based query failed to count only today's roasts for user!")

        # Run the refactored range-based query for anonymous user (ip = '127.0.0.1', user_id IS NULL)
        # Clear/insert anonymous roasts
        cursor.execute("DELETE FROM roasts")
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (NULL, '127.0.0.1', 'anon today', '{}', ?)
        ''', (today_now,))
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (NULL, '127.0.0.1', 'anon yesterday', '{}', ?)
        ''', (yesterday,))
        self.db_conn.commit()

        cursor.execute('''
            SELECT COUNT(*) FROM roasts
            WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')
        ''', ('127.0.0.1',))
        count_anon = cursor.fetchone()[0]
        self.assertEqual(count_anon, 1, "Range-based query failed to count only today's roasts for anonymous user!")

    def test_basic_routes(self):
        """Test that index page is reachable and returns HTTP 200."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/signup')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
