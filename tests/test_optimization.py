import os
import unittest
import sqlite3
import tempfile
import json

# Target isolated test database
os.environ['VERCEL'] = '1'
import app.routes as routes
from app import create_app

class TestDatabaseOptimization(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.original_db_path = routes.DB_PATH
        routes.DB_PATH = self.temp_db.name
        routes.init_db()

        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def tearDown(self):
        routes.DB_PATH = self.original_db_path
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_indexes_exist(self):
        """Verify that composite indexes were created in SQLite."""
        conn = routes.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row['name'] for row in cursor.fetchall()}
        conn.close()

        self.assertIn('idx_roasts_user_created', indexes)
        self.assertIn('idx_roasts_ip_user_created', indexes)

    def test_query_plan_uses_index(self):
        """Verify that SQLite EXPLAIN QUERY PLAN uses the composite indexes instead of full table scans."""
        conn = routes.get_db_connection()
        cursor = conn.cursor()

        # Check logged-in user rate limit query plan
        cursor.execute("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM roasts WHERE user_id = ? AND created_at >= date('now')", (1,))
        plan_logged_in = [row[3] for row in cursor.fetchall()]
        self.assertTrue(any('idx_roasts_user_created' in step for step in plan_logged_in), f"Expected index use, got: {plan_logged_in}")

        # Check anonymous IP rate limit query plan
        cursor.execute("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM roasts WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')", ('127.0.0.1',))
        plan_ip = [row[3] for row in cursor.fetchall()]
        self.assertTrue(any('idx_roasts_ip_user_created' in step for step in plan_ip), f"Expected index use, got: {plan_ip}")

        # Check user history ordering query plan
        cursor.execute("EXPLAIN QUERY PLAN SELECT id, user_input, roast_result, created_at FROM roasts WHERE user_id = ? ORDER BY created_at DESC", (1,))
        plan_history = [row[3] for row in cursor.fetchall()]
        self.assertTrue(any('idx_roasts_user_created' in step for step in plan_history), f"Expected index use, got: {plan_history}")

        conn.close()

    def test_rate_limiting_with_optimized_query(self):
        """Verify that the 3-roast daily cap works accurately under optimized range queries."""
        conn = routes.get_db_connection()
        cursor = conn.cursor()

        # Insert 3 roasts for today
        for i in range(3):
            cursor.execute(
                "INSERT INTO roasts (user_id, ip_address, user_input, roast_result) VALUES (?, ?, ?, ?)",
                (None, '127.0.0.1', f'Startup idea {i}', json.dumps({'headline': 'test'}))
            )
        conn.commit()
        conn.close()

        # POST another roast from the same IP (unauthenticated)
        response = self.client.post('/', data={'user_input': 'Another startup idea'})
        self.assertEqual(response.status_code, 200)
        # Should inform the user of daily rate limit reached
        self.assertIn(b'Rate Limit Exceeded', response.data)
        self.assertIn(b'3 / 3 Daily Limit', response.data)

if __name__ == '__main__':
    unittest.main()
