import unittest
import sqlite3
import os
import json
from app import create_app
from app.routes import DB_PATH, init_db, get_db_connection

class TestRoutesAndPerformance(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        # Ensure database is initialized
        init_db()

    def test_database_indexes_exist(self):
        """Verify that our optimized high-performance indexes exist on the roasts table."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='roasts'")
        indexes = [row['name'] for row in cursor.fetchall()]
        conn.close()

        self.assertIn('idx_roasts_user_created', indexes)
        self.assertIn('idx_roasts_ip_user_created', indexes)

    def test_query_plan_uses_index(self):
        """Verify that the optimized range queries utilize the composite index."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Explain Query Plan for logged-in user lookup
        cursor.execute("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM roasts WHERE user_id = ? AND created_at >= date('now')", (1,))
        plan_user = " ".join([row[3] for row in cursor.fetchall()])

        # Explain Query Plan for anonymous/IP-based user lookup
        cursor.execute("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM roasts WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')", ("127.0.0.1",))
        plan_ip = " ".join([row[3] for row in cursor.fetchall()])

        conn.close()

        # Ensure both query plans perform a search using a covering index instead of a full table scan
        self.assertIn("USING COVERING INDEX idx_roasts_user_created", plan_user)
        self.assertIn("USING COVERING INDEX idx_roasts_ip_user_created", plan_ip)

    def test_pages_load(self):
        """Verify that general routing functionality remains perfectly intact."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
