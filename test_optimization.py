import os
import unittest
import sqlite3
import json
from app import create_app
from app.routes import DB_PATH, init_db

class TestPerformanceOptimization(unittest.TestCase):
    def setUp(self):
        # Force a fresh database for testing
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def tearDown(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    def test_indexes_exist(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA index_list('roasts')")
        indexes = {row[1] for row in cursor.fetchall()}
        conn.close()

        self.assertIn('idx_roasts_user_created', indexes)
        self.assertIn('idx_roasts_ip_user_created', indexes)
        print("✅ Success: Composite indexes exist in database schema.")

    def test_explain_query_plan(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Insert some dummy records
        for i in range(10):
            cursor.execute('''
                INSERT INTO roasts (user_id, ip_address, user_input, roast_result)
                VALUES (?, ?, ?, ?)
            ''', (1 if i % 2 == 0 else None, f"192.168.1.{i}", "test", "{}"))
        conn.commit()

        # Query 1: User ID rate-limit query with range-based filter
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT COUNT(*) FROM roasts
            WHERE user_id = ? AND created_at >= date('now')
        ''', (1,))
        plan_user = cursor.fetchall()
        print("Explain Plan User Limit:", plan_user)
        # Check that it uses index
        using_index_user = any("idx_roasts_user_created" in row[3] for row in plan_user)
        self.assertTrue(using_index_user, "User limit query should use index idx_roasts_user_created")

        # Query 2: IP address rate-limit query with range-based filter
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT COUNT(*) FROM roasts
            WHERE ip_address = ? AND user_id IS NULL AND created_at >= date('now')
        ''', ("192.168.1.1",))
        plan_ip = cursor.fetchall()
        print("Explain Plan IP Limit:", plan_ip)
        using_index_ip = any("idx_roasts_ip_user_created" in row[3] for row in plan_ip)
        self.assertTrue(using_index_ip, "IP limit query should use index idx_roasts_ip_user_created")

        # Query 3: History load query
        cursor.execute('''
            EXPLAIN QUERY PLAN
            SELECT id, user_input, roast_result, created_at
            FROM roasts
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (1,))
        plan_history = cursor.fetchall()
        print("Explain Plan History:", plan_history)
        using_index_history = any("idx_roasts_user_created" in row[3] for row in plan_history)
        self.assertTrue(using_index_history, "History fetch query should use index idx_roasts_user_created")

        conn.close()
        print("✅ Success: EXPLAIN QUERY PLAN confirms index usage!")

    def test_flask_app_rate_limiting(self):
        # Verify the application still works correctly with the optimized query
        # Let's hit '/' multiple times
        # Since we do not have OPENROUTER_API_KEY, it will fallback to mock responses which saves roasts to database
        for _ in range(3):
            res = self.client.post('/', data={
                'user_input': 'My awesome micro-SaaS',
                'intensity': 'Savage',
                'personality': 'Tech Bro'
            })
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Substack for ADHD-addled attention spans', res.data)
            self.assertNotIn(b'daily cap', res.data)  # Limit shouldn't be reached yet

        # 4th hit should trigger daily cap limit_reached = True
        res = self.client.post('/', data={
            'user_input': 'Another idea',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        })
        self.assertEqual(res.status_code, 200)
        # Should inform that 3-roast daily cap is reached
        self.assertIn(b'Rate Limit Exceeded', res.data)
        print("✅ Success: Flask app rate-limiting correctly triggered after 3 requests!")

if __name__ == '__main__':
    unittest.main()
