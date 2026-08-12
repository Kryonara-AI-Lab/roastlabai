import os
import unittest
import sqlite3
import json
from app import create_app
from app.routes import DB_PATH, get_db_connection

class TestDatabaseOptimization(unittest.TestCase):
    def setUp(self):
        # Create Flask app and push context
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app_context.pop()

    def test_database_indexes_exist(self):
        """Verify that the high-performance composite indexes are created successfully."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Retrieve list of indexes
        cursor.execute("PRAGMA index_list('roasts')")
        indexes = [row['name'] for row in cursor.fetchall()]

        self.assertIn('idx_roasts_user_created', indexes, "Composite index idx_roasts_user_created is missing!")
        self.assertIn('idx_roasts_ip_user_created', indexes, "Composite index idx_roasts_ip_user_created is missing!")

        conn.close()

    def test_query_plans_use_indexes(self):
        """Verify using EXPLAIN QUERY PLAN that SQLite optimizes our queries using the composite indexes."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. User rate limit check query plan
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT COUNT(*) FROM roasts
            WHERE user_id = ? AND created_at >= date('now')
        ''', (1,))
        plan_user_limit = [row[3] for row in cursor.fetchall()]
        plan_user_str = " ".join(plan_user_limit)

        self.assertIn('idx_roasts_user_created', plan_user_str)
        self.assertIn('SEARCH', plan_user_str)
        # Ensure it does a range or equality search with the key, not a full index scan
        self.assertIn('user_id=?', plan_user_str)

        # 2. IP guest rate limit check query plan
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT COUNT(*) FROM roasts
            WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')
        ''', ('127.0.0.1',))
        plan_ip_limit = [row[3] for row in cursor.fetchall()]
        plan_ip_str = " ".join(plan_ip_limit)

        self.assertIn('idx_roasts_ip_user_created', plan_ip_str)
        self.assertIn('SEARCH', plan_ip_str)
        self.assertIn('ip_address=?', plan_ip_str)

        # 3. History query plan (must use index and avoid temp B-Tree filesort)
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT id, user_input, roast_result, created_at
            FROM roasts
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (1,))
        plan_history = [row[3] for row in cursor.fetchall()]
        plan_history_str = " ".join(plan_history)

        self.assertIn('idx_roasts_user_created', plan_history_str)
        self.assertIn('SEARCH', plan_history_str)
        self.assertNotIn('USE TEMP B-TREE FOR ORDER BY', plan_history_str, "Temp B-Tree sort should be avoided!")

        conn.close()

    def test_rate_limiting_functional_integrity(self):
        """Ensure rate limit lookup logic functions exactly as before with the optimized queries."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Let's insert mock roasts
        # Clean current roasts to have a predictable test environment
        cursor.execute("DELETE FROM roasts")

        # Guest roasts
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (NULL, '10.0.0.1', 'test guest', '{"score": 10}', datetime('now'))
        ''')
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (NULL, '10.0.0.1', 'test guest 2', '{"score": 20}', datetime('now'))
        ''')
        # An older guest roast (yesterday)
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (NULL, '10.0.0.1', 'old guest', '{"score": 30}', datetime('now', '-1 day'))
        ''')

        # Logged-in user roasts
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (42, '10.0.0.2', 'user roast 1', '{"score": 50}', datetime('now'))
        ''')
        cursor.execute('''
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (42, '10.0.0.2', 'old user roast', '{"score": 60}', datetime('now', '-2 days'))
        ''')

        conn.commit()

        # Test guest count for today (should be 2, ignoring the one from yesterday)
        cursor.execute('''
            SELECT COUNT(*) FROM roasts
            WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')
        ''', ('10.0.0.1',))
        guest_count = cursor.fetchone()[0]
        self.assertEqual(guest_count, 2)

        # Test logged-in user count for today (should be 1, ignoring the older roast)
        cursor.execute('''
            SELECT COUNT(*) FROM roasts
            WHERE user_id = ? AND created_at >= date('now')
        ''', (42,))
        user_count = cursor.fetchone()[0]
        self.assertEqual(user_count, 1)

        # Clean up database after functional test
        cursor.execute("DELETE FROM roasts")
        conn.commit()
        conn.close()

if __name__ == '__main__':
    unittest.main()
