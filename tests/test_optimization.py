import unittest
import sqlite3
import tempfile
import os

os.environ['VERCEL'] = '1'
import app.routes

class TestDatabaseOptimization(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()

        self.orig_db_path = app.routes.DB_PATH
        app.routes.DB_PATH = self.db_path
        app.routes.init_db()

    def tearDown(self):
        app.routes.DB_PATH = self.orig_db_path
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_composite_indexes_exist(self):
        conn = app.routes.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row['name'] for row in cursor.fetchall()}
        conn.close()

        self.assertIn('idx_roasts_user_created', indexes)
        self.assertIn('idx_roasts_ip_user_created', indexes)

    def test_query_plan_uses_index_for_user_rate_limit(self):
        conn = app.routes.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT COUNT(*) FROM roasts
            WHERE user_id = ? AND created_at >= date('now')
        ''', (1,))
        plan_rows = [row[3] if len(row) > 3 else str(row) for row in cursor.fetchall()]
        conn.close()

        plan_str = " ".join(plan_rows)
        self.assertIn("USING COVERING INDEX idx_roasts_user_created", plan_str)
        self.assertNotIn("SCAN roasts", plan_str)

    def test_query_plan_uses_index_for_ip_rate_limit(self):
        conn = app.routes.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT COUNT(*) FROM roasts
            WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')
        ''', ('127.0.0.1',))
        plan_rows = [row[3] if len(row) > 3 else str(row) for row in cursor.fetchall()]
        conn.close()

        plan_str = " ".join(plan_rows)
        self.assertIn("USING COVERING INDEX idx_roasts_ip_user_created", plan_str)
        self.assertNotIn("SCAN roasts", plan_str)

    def test_query_plan_uses_index_for_user_history(self):
        conn = app.routes.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT id, user_input, roast_result, created_at
            FROM roasts
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (1,))
        plan_rows = [row[3] if len(row) > 3 else str(row) for row in cursor.fetchall()]
        conn.close()

        plan_str = " ".join(plan_rows)
        self.assertIn("USING INDEX idx_roasts_user_created", plan_str)
        self.assertNotIn("USE TEMP B-TREE", plan_str)
        self.assertNotIn("SCAN roasts", plan_str)

    def test_rate_limit_logic_correctness(self):
        conn = app.routes.get_db_connection()
        cursor = conn.cursor()

        # Insert 1 entry from today
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', (1, '127.0.0.1', 'test input 1', '{}'))

        # Insert 1 entry from yesterday
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (?, ?, ?, ?, datetime('now', '-1 day'))
        ''', (1, '127.0.0.1', 'test input old', '{}'))

        conn.commit()

        # User rate limit check
        cursor.execute('''
            SELECT COUNT(*) FROM roasts
            WHERE user_id = ? AND created_at >= date('now')
        ''', (1,))
        self.assertEqual(cursor.fetchone()[0], 1)

        # IP rate limit check (null user_id)
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', (None, '192.168.1.1', 'anon test 1', '{}'))
        conn.commit()

        cursor.execute('''
            SELECT COUNT(*) FROM roasts
            WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')
        ''', ('192.168.1.1',))
        self.assertEqual(cursor.fetchone()[0], 1)

        conn.close()

if __name__ == '__main__':
    unittest.main()
