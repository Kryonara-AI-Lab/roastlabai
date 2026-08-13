import os
import sqlite3
import unittest
from app.routes import DB_PATH, init_db

class TestDatabaseOptimization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize database to make sure tables and indexes exist
        init_db()

    def get_db_cursor(self):
        conn = sqlite3.connect(DB_PATH)
        return conn, conn.cursor()

    def test_indexes_exist(self):
        conn, cursor = self.get_db_cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall() if row[0] is not None]
        conn.close()

        self.assertIn('idx_roasts_user_created', indexes, "Index 'idx_roasts_user_created' missing")
        self.assertIn('idx_roasts_ip_user_created', indexes, "Index 'idx_roasts_ip_user_created' missing")

    def test_user_history_query_plan(self):
        conn, cursor = self.get_db_cursor()
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT id, user_input, roast_result, created_at
            FROM roasts
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (1,))
        plan = cursor.fetchall()
        conn.close()

        # Check if the query uses the index instead of a full table scan and temp B-Tree sort
        plan_str = " ".join([row[3] for row in plan])
        self.assertIn('idx_roasts_user_created', plan_str, f"Query did not use idx_roasts_user_created: {plan_str}")
        self.assertNotIn('USE TEMP B-TREE', plan_str, "Query uses a temporary B-Tree for sorting")

    def test_user_rate_limit_query_plan(self):
        conn, cursor = self.get_db_cursor()
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT COUNT(*) FROM roasts
            WHERE user_id = ? AND created_at >= date('now')
        ''', (1,))
        plan = cursor.fetchall()
        conn.close()

        plan_str = " ".join([row[3] for row in plan])
        self.assertIn('idx_roasts_user_created', plan_str, f"Query did not use idx_roasts_user_created: {plan_str}")
        self.assertIn('SEARCH', plan_str, "Query did not perform an index search")

    def test_ip_rate_limit_query_plan(self):
        conn, cursor = self.get_db_cursor()
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT COUNT(*) FROM roasts
            WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')
        ''', ('127.0.0.1',))
        plan = cursor.fetchall()
        conn.close()

        plan_str = " ".join([row[3] for row in plan])
        self.assertIn('idx_roasts_ip_user_created', plan_str, f"Query did not use idx_roasts_ip_user_created: {plan_str}")
        self.assertIn('SEARCH', plan_str, "Query did not perform an index search")

if __name__ == '__main__':
    unittest.main()
