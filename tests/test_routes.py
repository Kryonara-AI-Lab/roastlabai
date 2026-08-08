import os
import sqlite3
import unittest
import json
from unittest.mock import patch

# Set a test environment variable or patch DB_PATH before importing app modules
# to avoid modifying the tracked production/development SQLite file.
TEST_DB_PATH = '/tmp/roastlab_test.db'

with patch('app.routes.DB_PATH', TEST_DB_PATH):
    from app import create_app
    from app.routes import init_db, get_db_connection

class TestRoutesAndIndexes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure test database is clean and initialized
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)

        # Patch the DB_PATH during init_db()
        with patch('app.routes.DB_PATH', TEST_DB_PATH):
            init_db()

    @classmethod
    def tearDownClass(cls):
        # Clean up test database file
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except OSError:
                pass

    def setUp(self):
        # Patch DB_PATH during app creation and request context execution
        self.db_patcher = patch('app.routes.DB_PATH', TEST_DB_PATH)
        self.db_patcher.start()

        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.ctx = self.app.test_request_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()
        self.db_patcher.stop()

    def test_indexes_exist(self):
        """Verify that the required performance composite indexes exist in the database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row['name'] for row in cursor.fetchall()]
        conn.close()

        self.assertIn('idx_roasts_user_created', indexes)
        self.assertIn('idx_roasts_ip_user_created', indexes)

    def test_query_plan_authenticated_rate_limit(self):
        """Verify that the rate limit query for authenticated users uses the composite index."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # EXPLAIN QUERY PLAN for user rate limiting query
        query = "SELECT COUNT(*) FROM roasts WHERE user_id = ? AND created_at >= date('now')"
        cursor.execute(f"EXPLAIN QUERY PLAN {query}", (1,))
        plan = cursor.fetchall()
        conn.close()

        # The query plan must use the composite index idx_roasts_user_created
        plan_str = " ".join([row[3] for row in plan]).lower()
        self.assertIn("idx_roasts_user_created", plan_str)
        self.assertNotIn("scan roasts", plan_str)

    def test_query_plan_anonymous_rate_limit(self):
        """Verify that the rate limit query for anonymous users uses the composite index."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # EXPLAIN QUERY PLAN for anonymous rate limiting query
        query = "SELECT COUNT(*) FROM roasts WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')"
        cursor.execute(f"EXPLAIN QUERY PLAN {query}", ("127.0.0.1",))
        plan = cursor.fetchall()
        conn.close()

        # The query plan must use the composite index idx_roasts_ip_user_created
        plan_str = " ".join([row[3] for row in plan]).lower()
        self.assertIn("idx_roasts_ip_user_created", plan_str)
        self.assertNotIn("scan roasts", plan_str)

    def test_query_plan_history_load(self):
        """Verify that history loading uses the index without scanning the entire table or using a temporary sorting B-Tree."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # EXPLAIN QUERY PLAN for history loading query
        query = "SELECT id, user_input, roast_result, created_at FROM roasts WHERE user_id = ? ORDER BY created_at DESC"
        cursor.execute(f"EXPLAIN QUERY PLAN {query}", (1,))
        plan = cursor.fetchall()
        conn.close()

        # The query plan must use the composite index and must NOT require a temporary sort table
        plan_str = " ".join([row[3] for row in plan]).lower()
        self.assertIn("idx_roasts_user_created", plan_str)
        self.assertNotIn("temp b-tree", plan_str)

    def test_rate_limiting_functionality(self):
        """Test that the 3-roast daily cap is correctly enforced and functional."""
        # Insert 3 fake roasts for an anonymous user from IP '127.0.0.1'
        conn = get_db_connection()
        cursor = conn.cursor()

        # Clean current roasts to ensure accurate test
        cursor.execute("DELETE FROM roasts")

        for i in range(3):
            cursor.execute(
                "INSERT INTO roasts (user_id, ip_address, user_input, roast_result) VALUES (NULL, '127.0.0.1', 'idea', '{}')"
            )
        conn.commit()
        conn.close()

        # Try to make another request via the Flask test client
        # To simulate the POST request, we use the client
        response = self.client.post('/', data={
            'user_input': 'another brilliant startup idea',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        }, headers={'X-Forwarded-For': '127.0.0.1'})

        # The page should show the limit reached banner / message
        html_content = response.data.decode('utf-8')
        self.assertIn("Hold your horses, founder.", html_content)

if __name__ == '__main__':
    unittest.main()
