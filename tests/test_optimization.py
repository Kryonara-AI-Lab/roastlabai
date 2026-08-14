import unittest
import sqlite3
import os
import tempfile

# Force Vercel env or custom DB path before routes import to avoid touching production DB
os.environ['VERCEL'] = '1'

import app.routes as routes

class TestDatabaseOptimization(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        routes.DB_PATH = self.db_path
        routes.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_query_plan_uses_indexes(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Explain query plan for logged in rate limit check
        cursor.execute("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM roasts WHERE user_id = ? AND created_at >= date('now')", (1,))
        plan_logged_in = cursor.fetchall()

        # Explain query plan for anonymous rate limit check
        cursor.execute("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM roasts WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')", ('127.0.0.1',))
        plan_anon = cursor.fetchall()

        # Explain query plan for history query
        cursor.execute("EXPLAIN QUERY PLAN SELECT id, user_input, roast_result, created_at FROM roasts WHERE user_id = ? ORDER BY created_at DESC", (1,))
        plan_history = cursor.fetchall()

        conn.close()

        # Verify that SEARCH using INDEX or COVERING INDEX is used (no SCAN roasts)
        logged_in_plan_str = str(plan_logged_in)
        anon_plan_str = str(plan_anon)
        history_plan_str = str(plan_history)

        self.assertIn("SEARCH", logged_in_plan_str)
        self.assertIn("idx_roasts_user_created", logged_in_plan_str)

        self.assertIn("SEARCH", anon_plan_str)
        self.assertIn("idx_roasts_ip_user_created", anon_plan_str)

        self.assertIn("SEARCH", history_plan_str)
        self.assertNotIn("USE TEMP B-TREE FOR ORDER BY", history_plan_str)

if __name__ == '__main__':
    unittest.main()
