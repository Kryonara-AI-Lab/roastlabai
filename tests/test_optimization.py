import os
import unittest
import tempfile
import sqlite3

# Set VERCEL to ensure routes uses an isolated test DB path or override DB_PATH
os.environ['VERCEL'] = '1'

import app.routes as routes

class TestDatabaseOptimization(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        routes.DB_PATH = self.db_path
        routes.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_indexes_exist(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.assertIn('idx_roasts_user_created', indexes)
        self.assertIn('idx_roasts_ip_user_created', indexes)

    def test_query_plan_uses_index(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check logged-in user rate-limit query plan
        cursor.execute("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM roasts WHERE user_id = ? AND created_at >= date('now')", (1,))
        plan_user = cursor.fetchall()
        user_plan_str = " ".join([str(p) for p in plan_user])
        self.assertIn("idx_roasts_user_created", user_plan_str)
        self.assertIn("SEARCH roasts", user_plan_str)

        # Check anonymous IP rate-limit query plan
        cursor.execute("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM roasts WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')", ("127.0.0.1",))
        plan_ip = cursor.fetchall()
        ip_plan_str = " ".join([str(p) for p in plan_ip])
        self.assertIn("idx_roasts_ip_user_created", ip_plan_str)
        self.assertIn("SEARCH roasts", ip_plan_str)

        conn.close()

if __name__ == '__main__':
    unittest.main()
