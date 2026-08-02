import os
import unittest
import sqlite3
import json
from app import create_app
from app.routes import DB_PATH, init_db, get_db_connection

class RoastLabTestCase(unittest.TestCase):
    def setUp(self):
        # Set up test app
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_secret'
        self.client = self.app.test_client()

        # Ensure database is initialized
        init_db()

    def test_database_indexes_exist(self):
        """Verify that the Bolt performance composite indexes exist in the database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
        indexes = {row['name'] for row in cursor.fetchall()}
        conn.close()

        self.assertIn('idx_roasts_user_created', indexes)
        self.assertIn('idx_roasts_ip_user_created', indexes)

    def test_static_routes_render(self):
        """Verify that general content routes load successfully."""
        routes = [
            '/',
            '/login',
            '/signup',
            '/privacy.html',
            '/terms.html',
            '/Model.html',
            '/company/manifesto',
            '/company/pricing'
        ]
        for route in routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200)

    def test_range_query_rate_limiting_logic(self):
        """Test rate limiting range-based queries directly in SQL."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Clear existing test entries for clean run
        cursor.execute("DELETE FROM roasts")
        conn.commit()

        # Insert test roasts (2 today, 1 yesterday)
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (999, '127.0.0.1', 'idea1', '{}', datetime('now'))
        ''')
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (999, '127.0.0.1', 'idea2', '{}', datetime('now'))
        ''')
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (999, '127.0.0.1', 'idea3', '{}', datetime('now', '-1 day'))
        ''')
        conn.commit()

        # Query count for today using range condition
        cursor.execute('''
            SELECT COUNT(*) FROM roasts
            WHERE user_id = 999 AND created_at >= date('now')
        ''')
        count = cursor.fetchone()[0]
        self.assertEqual(count, 2)

        conn.close()

if __name__ == '__main__':
    unittest.main()
