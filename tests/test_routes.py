import os
import sqlite3
import unittest
from flask import session
from app import create_app
from app.routes import DB_PATH, init_db, get_db_connection

class RoastLabPerformanceTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        # Set up a clean test database file
        self.test_db_path = os.path.join(os.path.dirname(__file__), 'test_roastlab.db')
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except OSError:
                pass

        # Override the DB_PATH for testing
        import app.routes
        self.original_db_path = app.routes.DB_PATH
        app.routes.DB_PATH = self.test_db_path

        # Initialize test database
        init_db()

    def tearDown(self):
        import app.routes
        app.routes.DB_PATH = self.original_db_path
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except OSError:
                pass

    def test_database_indexes_exist(self):
        """Verify that the optimized composite indexes are successfully created."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Retrieve all indexes on the 'roasts' table
        cursor.execute("PRAGMA index_list(roasts)")
        indexes = [row['name'] for row in cursor.fetchall()]

        self.assertIn('idx_roasts_user_created', indexes, "idx_roasts_user_created should exist")
        self.assertIn('idx_roasts_ip_user_created', indexes, "idx_roasts_ip_user_created should exist")
        conn.close()

    def test_explain_query_plan_user_limit(self):
        """Verify that the rate limit query for users uses the idx_roasts_user_created index."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Use EXPLAIN QUERY PLAN to check if index is used
        query = '''
            SELECT COUNT(*) FROM roasts
            WHERE user_id = ? AND created_at >= date('now')
        '''
        cursor.execute(f"EXPLAIN QUERY PLAN {query}", (1,))
        plan_steps = [row[3] for row in cursor.fetchall()]
        plan_string = " ".join(plan_steps)

        # Verify that SQLite uses the composite index rather than a SCAN (full table scan)
        self.assertIn('idx_roasts_user_created', plan_string, f"Query plan should utilize idx_roasts_user_created. Plan: {plan_string}")
        self.assertNotIn('SCAN roasts', plan_string, f"Query plan should not perform a full SCAN. Plan: {plan_string}")
        conn.close()

    def test_explain_query_plan_ip_limit(self):
        """Verify that the rate limit query for IPs uses the idx_roasts_ip_user_created index."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Use EXPLAIN QUERY PLAN to check if index is used
        query = '''
            SELECT COUNT(*) FROM roasts
            WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')
        '''
        cursor.execute(f"EXPLAIN QUERY PLAN {query}", ('127.0.0.1',))
        plan_steps = [row[3] for row in cursor.fetchall()]
        plan_string = " ".join(plan_steps)

        # Verify that SQLite uses the composite index rather than a SCAN (full table scan)
        self.assertIn('idx_roasts_ip_user_created', plan_string, f"Query plan should utilize idx_roasts_ip_user_created. Plan: {plan_string}")
        self.assertNotIn('SCAN roasts', plan_string, f"Query plan should not perform a full SCAN. Plan: {plan_string}")
        conn.close()

    def test_explain_query_plan_history(self):
        """Verify that the history loading query uses the idx_roasts_user_created index and avoids sorting."""
        conn = get_db_connection()
        cursor = conn.cursor()

        query = '''
            SELECT id, user_input, roast_result, created_at
            FROM roasts
            WHERE user_id = ?
            ORDER BY created_at DESC
        '''
        cursor.execute(f"EXPLAIN QUERY PLAN {query}", (1,))
        plan_steps = [row[3] for row in cursor.fetchall()]
        plan_string = " ".join(plan_steps)

        # SQLite should use the composite index (which already provides sorting by created_at)
        self.assertIn('idx_roasts_user_created', plan_string, f"Query plan should utilize idx_roasts_user_created. Plan: {plan_string}")
        self.assertNotIn('USE TEMP B-TREE FOR ORDER BY', plan_string, f"Query should use index for ordering. Plan: {plan_string}")
        conn.close()

    def test_main_page_renders(self):
        """Verify basic route integrity is maintained."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
