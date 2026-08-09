import unittest
import os
import sqlite3
import json
from app import create_app
from app.routes import DB_PATH, get_db_connection, init_db

class RoastLabPerformanceTestCase(unittest.TestCase):
    def setUp(self):
        # Set up a test application and configure it
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = self.app.test_client()

        # Use an in-memory database or temporary database for testing to avoid touching production data
        self.db_fd = None
        # We can dynamically override the DB_PATH or re-initialize a clean test database file.
        # But for index testing, we can simply inspect the database pointed to by DB_PATH.
        # Let's ensure the DB is initialized.
        init_db()

    def test_database_indexes_exist(self):
        """Test that the required high-performance composite indexes are created in SQLite."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Retrieve all indexes on the roasts table
        cursor.execute("PRAGMA index_list('roasts')")
        indexes = cursor.fetchall()
        index_names = [idx['name'] for idx in indexes]

        self.assertIn('idx_roasts_user_created', index_names, "Missing composite index: idx_roasts_user_created")
        self.assertIn('idx_roasts_ip_user_created', index_names, "Missing composite index: idx_roasts_ip_user_created")

        # Verify columns of idx_roasts_user_created
        cursor.execute("PRAGMA index_info('idx_roasts_user_created')")
        cols = [info['name'] for info in cursor.fetchall()]
        self.assertEqual(cols, ['user_id', 'created_at'], "idx_roasts_user_created should index (user_id, created_at)")

        # Verify columns of idx_roasts_ip_user_created
        cursor.execute("PRAGMA index_info('idx_roasts_ip_user_created')")
        cols_ip = [info['name'] for info in cursor.fetchall()]
        self.assertEqual(cols_ip, ['ip_address', 'user_id', 'created_at'], "idx_roasts_ip_user_created should index (ip_address, user_id, created_at)")

        conn.close()

    def test_query_plans_use_indexes(self):
        """Explain Query Plan assertions to guarantee that SQLite avoids table scans and file-sorts."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Check logged-in rate limit query plan
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT COUNT(*) FROM roasts
            WHERE user_id = ? AND created_at >= date('now')
        ''', (1,))
        plan = " ".join([row[3] for row in cursor.fetchall()]).lower()
        self.assertIn("idx_roasts_user_created", plan,
                      f"Expected rate limit query to use idx_roasts_user_created. Plan: {plan}")

        # 2. Check anonymous rate limit query plan
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT COUNT(*) FROM roasts
            WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')
        ''', ('127.0.0.1',))
        plan = " ".join([row[3] for row in cursor.fetchall()]).lower()
        self.assertIn("idx_roasts_ip_user_created", plan,
                      f"Expected anonymous rate limit query to use idx_roasts_ip_user_created. Plan: {plan}")

        # 3. Check history loading query plan (specifically testing ORDER BY)
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT id, user_input, roast_result, created_at
            FROM roasts
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (1,))
        plan_rows = cursor.fetchall()
        plan_desc = " ".join([row[3] for row in plan_rows]).lower()

        # Verify index usage
        self.assertIn("idx_roasts_user_created", plan_desc,
                      f"Expected history loading query to use idx_roasts_user_created index. Plan: {plan_desc}")

        # Verify that SQLite avoids a separate sorting pass because the index is already sorted
        self.assertNotIn("use temp b-tree for order by", plan_desc,
                         f"Performance Warning: Query plan required a temp b-tree sort! Plan: {plan_desc}")

        conn.close()

    def test_homepage_loads_correctly(self):
        """Verify that the home page returns 200 OK."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_compliance_and_company_pages_load(self):
        """Verify static compliance and company pages return 200 OK."""
        routes = [
            '/privacy.html',
            '/terms.html',
            '/DCL.html',
            '/Model.html',
            '/company/manifesto',
            '/company/pricing',
            '/company/protocol',
            '/company/logs'
        ]
        for r in routes:
            response = self.client.get(r)
            self.assertEqual(response.status_code, 200, f"Failed to load: {r}")

if __name__ == '__main__':
    unittest.main()
