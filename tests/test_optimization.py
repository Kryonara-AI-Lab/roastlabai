import os
import sqlite3
import tempfile
import unittest

# Ensure VERCEL env is set so routes uses /tmp or temp DB location during testing
os.environ['VERCEL'] = '1'

import app.routes
from app import create_app


class OptimizationTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.routes.DB_PATH = self.db_path
        app.routes.init_db()

        self.flask_app = create_app()
        self.flask_app.config['TESTING'] = True
        self.client = self.flask_app.test_client()

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_query_execution_plan_uses_indexes(self):
        conn = app.routes.get_db_connection()
        cursor = conn.cursor()

        # Check user query plan
        cursor.execute(
            "EXPLAIN QUERY PLAN SELECT COUNT(*) FROM roasts WHERE user_id = ? AND created_at >= date('now')",
            (1,)
        )
        user_plan = " ".join([row[3] for row in cursor.fetchall()])
        self.assertIn("USING COVERING INDEX idx_roasts_user_created", user_plan)

        # Check IP query plan
        cursor.execute(
            "EXPLAIN QUERY PLAN SELECT COUNT(*) FROM roasts WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')",
            ("127.0.0.1",)
        )
        ip_plan = " ".join([row[3] for row in cursor.fetchall()])
        self.assertIn("USING COVERING INDEX idx_roasts_ip_user_created", ip_plan)

        # Check user history query plan
        cursor.execute(
            "EXPLAIN QUERY PLAN SELECT id, user_input, roast_result, created_at FROM roasts WHERE user_id = ? ORDER BY created_at DESC",
            (1,)
        )
        history_plan = " ".join([row[3] for row in cursor.fetchall()])
        self.assertIn("USING INDEX idx_roasts_user_created", history_plan)

        conn.close()

    def test_routes_functionality(self):
        # GET homepage
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)

        # POST roast submission
        res = self.client.post('/', data={
            'user_input': 'Test startup idea for automated code testing',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'roast', res.data.lower())


if __name__ == '__main__':
    unittest.main()
