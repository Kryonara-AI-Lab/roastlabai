import os
import sqlite3
import unittest

os.environ['VERCEL'] = '1'

import app.routes

class TestOptimization(unittest.TestCase):
    def setUp(self):
        self.test_db_path = '/tmp/roastlab_opt_test.db'
        app.routes.DB_PATH = self.test_db_path
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        app.routes.init_db()

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_explain_query_plans_use_indexes(self):
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()

        # Query 1: Logged-in user rate limit check
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT COUNT(*) FROM roasts
            WHERE user_id = ? AND created_at >= date('now')
        ''', (1,))
        plan1 = cursor.fetchall()
        plan1_str = str(plan1)
        self.assertIn('COVERING INDEX', plan1_str)
        self.assertIn('idx_roasts_user_created', plan1_str)

        # Query 2: Anonymous IP rate limit check
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT COUNT(*) FROM roasts
            WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')
        ''', ('127.0.0.1',))
        plan2 = cursor.fetchall()
        plan2_str = str(plan2)
        self.assertIn('COVERING INDEX', plan2_str)
        self.assertIn('idx_roasts_ip_user_created', plan2_str)

        # Query 3: History query by user_id ORDER BY created_at DESC
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT id, user_input, roast_result, created_at
            FROM roasts
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (1,))
        plan3 = cursor.fetchall()
        plan3_str = str(plan3)
        self.assertIn('idx_roasts_user_created', plan3_str)
        self.assertNotIn('TEMP B-TREE', plan3_str)

        conn.close()

if __name__ == '__main__':
    unittest.main()
