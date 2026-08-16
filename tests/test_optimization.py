import os
import unittest
import sqlite3

# Set VERCEL environment variable so init_db creates db at /tmp or test path
os.environ['VERCEL'] = '1'

import app.routes as routes

class TestDatabaseOptimization(unittest.TestCase):
    def setUp(self):
        # Use a temporary database for testing
        self.test_db_path = '/tmp/test_roastlab_opt.db'
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        routes.DB_PATH = self.test_db_path
        routes.init_db()

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_indexes_exist(self):
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.assertIn('idx_roasts_user_created', indexes)
        self.assertIn('idx_roasts_ip_user_created', indexes)

    def test_explain_query_plan_uses_index(self):
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # Query 1: Logged in user query
        cursor.execute(
            "EXPLAIN QUERY PLAN SELECT COUNT(*) FROM roasts WHERE user_id = ? AND created_at >= date('now')",
            (1,)
        )
        plan1 = " ".join([str(col) for row in cursor.fetchall() for col in row])
        self.assertIn('idx_roasts_user_created', plan1)

        # Query 2: Anonymous IP query
        cursor.execute(
            "EXPLAIN QUERY PLAN SELECT COUNT(*) FROM roasts WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')",
            ('127.0.0.1',)
        )
        plan2 = " ".join([str(col) for row in cursor.fetchall() for col in row])
        self.assertIn('idx_roasts_ip_user_created', plan2)

        conn.close()

if __name__ == '__main__':
    unittest.main()
