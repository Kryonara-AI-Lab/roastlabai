import unittest
import os
import tempfile
import sqlite3
import json
from app import create_app
from app.routes import DB_PATH, get_db_connection, init_db

class RoastLabPerformanceTests(unittest.TestCase):
    def setUp(self):
        # Create a temp database for testing
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.app = create_app()
        self.app.config['TESTING'] = True

        # Override the database path globally
        import app.routes
        self.original_db_path = app.routes.DB_PATH
        app.routes.DB_PATH = self.db_path

        # Re-initialize the test database
        app.routes.init_db()
        self.client = self.app.test_client()

    def tearDown(self):
        import app.routes
        app.routes.DB_PATH = self.original_db_path
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_routes_exist_and_render(self):
        """Verify basic routes render successfully."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/signup')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)

    def test_database_indexes_exist(self):
        """Verify the optimized composite indexes exist in the schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cursor.fetchall()}
        conn.close()

        self.assertIn('idx_roasts_user_created', indexes)
        self.assertIn('idx_roasts_ip_user_created', indexes)

    def test_rate_limit_query_uses_index(self):
        """Verify via EXPLAIN QUERY PLAN that our sargable queries use the composite indexes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Query 1: Logged-in user rate limiting check
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT COUNT(*) FROM roasts
            WHERE user_id = ? AND created_at >= date('now')
        ''', (1,))
        query_plan_1 = "\n".join([row[3] for row in cursor.fetchall()])

        # Query 2: Anonymous user rate limiting check
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT COUNT(*) FROM roasts
            WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')
        ''', ('127.0.0.1',))
        query_plan_2 = "\n".join([row[3] for row in cursor.fetchall()])

        conn.close()

        # Assert index usage (e.g. SEARCH TABLE roasts USING INDEX ...)
        self.assertIn("idx_roasts_user_created", query_plan_1)
        self.assertIn("idx_roasts_ip_user_created", query_plan_2)

if __name__ == '__main__':
    unittest.main()
