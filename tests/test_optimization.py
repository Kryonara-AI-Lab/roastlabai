import os
import sqlite3
import tempfile
import unittest

# Set VERCEL environment variable before importing routes so DB_PATH can be isolated
os.environ['VERCEL'] = '1'

from app import create_app
from app.routes import init_db, get_db_connection, DB_PATH

class TestDatabaseOptimization(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.temp_db_fd)

        # Override DB_PATH in routes module
        import app.routes
        self.original_db_path = app.routes.DB_PATH
        app.routes.DB_PATH = self.temp_db_path

        init_db()

        self.app = create_app()
        self.client = self.app.test_client()

    def tearDown(self):
        import app.routes
        app.routes.DB_PATH = self.original_db_path
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_indexes_exist(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.assertIn('idx_roasts_user_created', indexes)
        self.assertIn('idx_roasts_ip_user_created', indexes)

    def test_rate_limiting_query_performance_and_functionality(self):
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert 3 test roasts for an IP today
        ip = '127.0.0.1'
        for i in range(3):
            cursor.execute('''
                INSERT INTO roasts (user_id, ip_address, user_input, roast_result)
                VALUES (NULL, ?, ?, ?)
            ''', (ip, f'Test idea {i}', '{"headline": "Test"}'))
        conn.commit()

        # Verify EXPLAIN QUERY PLAN uses index on created_at range query
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT COUNT(*) FROM roasts
            WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')
        ''', (ip,))
        plan = cursor.fetchall()
        plan_str = " ".join(tuple(row)[-1] for row in plan)
        conn.close()

        # Check that index is referenced in query plan
        self.assertTrue('idx_roasts_ip_user_created' in plan_str or 'USING INDEX' in plan_str or 'USING COVERING INDEX' in plan_str)

        # Send POST request to test rate limiting trigger
        response = self.client.post('/', data={
            'user_input': 'Another idea after limit reached',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rate Limit Exceeded', response.data)

if __name__ == '__main__':
    unittest.main()
