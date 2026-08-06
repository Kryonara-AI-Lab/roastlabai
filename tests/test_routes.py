import os
import unittest
import sqlite3
import json
from app import create_app
import app.routes as routes

class TestRoutesAndDatabase(unittest.TestCase):
    def setUp(self):
        # Use a temporary database file for test isolation
        self.test_db_path = os.path.join(os.path.dirname(routes.__file__), 'test_roastlab.db')
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except OSError:
                pass

        # Save original DB_PATH and override with test path
        self.original_db_path = routes.DB_PATH
        routes.DB_PATH = self.test_db_path

        # Initialize the test database
        routes.init_db()

        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def tearDown(self):
        # Restore original DB_PATH
        routes.DB_PATH = self.original_db_path
        # Clean up the test database file
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except OSError:
                pass

    def test_indexes_exist(self):
        """Verify that our optimized composite indexes are properly created on the roasts table."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA index_list(roasts);")
        indexes = cursor.fetchall()
        conn.close()

        index_names = [idx[1] for idx in indexes]
        self.assertIn('idx_roasts_user_created', index_names, "idx_roasts_user_created was not created!")
        self.assertIn('idx_roasts_ip_user_created', index_names, "idx_roasts_ip_user_created was not created!")

    def test_query_plans_use_indexes(self):
        """Verify that SQLite uses our composite indexes (and covering index scan) for the optimized range queries."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # 1. Check user-based rate limit query plan
        cursor.execute("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM roasts WHERE user_id = 1 AND created_at >= date('now');")
        plan_user = cursor.fetchall()
        user_plan_detail = " ".join([row[3] for row in plan_user])

        # 2. Check IP-based rate limit query plan
        cursor.execute("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM roasts WHERE ip_address = '127.0.0.1' AND user_id IS NULL AND created_at >= date('now');")
        plan_ip = cursor.fetchall()
        ip_plan_detail = " ".join([row[3] for row in plan_ip])

        conn.close()

        # Assertions to ensure SEARCH (index lookup) and idx_roasts_user_created/idx_roasts_ip_user_created are used
        self.assertIn("SEARCH", user_plan_detail, "User-based query did not perform an index SEARCH!")
        self.assertIn("idx_roasts_user_created", user_plan_detail, "User-based query did not use idx_roasts_user_created index!")

        self.assertIn("SEARCH", ip_plan_detail, "IP-based query did not perform an index SEARCH!")
        self.assertIn("idx_roasts_ip_user_created", ip_plan_detail, "IP-based query did not use idx_roasts_ip_user_created index!")

    def test_rate_limiting_cap(self):
        """Verify that the daily rate limit of 3 roasts is properly enforced."""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # Populate 3 mock roasts for IP '127.0.0.1' with UTC timestamp representing 'today'
        # Default roast_result is valid JSON string
        dummy_result = json.dumps({"headline": "dummy"})
        for i in range(3):
            cursor.execute('''
                INSERT INTO roasts (user_id, ip_address, user_input, roast_result)
                VALUES (NULL, '127.0.0.1', 'dummy input', ?)
            ''', (dummy_result,))
        conn.commit()
        conn.close()

        # Perform the 4th request to trigger the limit check
        with self.client.session_transaction() as sess:
            # Not logged in
            sess.pop('user_id', None)

        response = self.client.post('/', data={
            'user_input': 'Fourth idea to roast',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        }, headers={'X-Forwarded-For': '127.0.0.1'})

        # The response page should mention "limit" or contain elements showing rate limit reached
        html_content = response.data.decode('utf-8')
        # Let's verify the form response contains indications of daily limit reached
        self.assertIn('limit', html_content.lower(), "Daily limit was not reached / displayed in the HTML content!")

if __name__ == '__main__':
    unittest.main()
