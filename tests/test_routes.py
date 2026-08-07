import os
import unittest
import json
import sqlite3
import tempfile
from flask import Flask

# Import the app factory or Blueprint registration
from app import create_app
from app.routes import DB_PATH, init_db
import app.routes as routes

class RoastLabTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file
        self.db_fd, self.temp_db_path = tempfile.mkstemp()

        # Monkeypatch routes.DB_PATH to use our temp test database
        self.original_db_path = routes.DB_PATH
        routes.DB_PATH = self.temp_db_path

        # Initialize the test database schema and indexes
        init_db()

        # Create and configure the app for testing
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-secret'
        self.client = self.app.test_client()

    def tearDown(self):
        # Restore original database path
        routes.DB_PATH = self.original_db_path

        # Close and unlink the temporary database file
        os.close(self.db_fd)
        os.unlink(self.temp_db_path)

    def test_database_indexes_exist(self):
        """Verify that our optimized composite indexes are successfully created."""
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        self.assertIn('idx_roasts_user_created', indexes)
        self.assertIn('idx_roasts_ip_user_created', indexes)

    def test_index_route_loads(self):
        """Verify that the landing page renders correctly."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'RoastLab', response.data)
        self.assertIn(b'Your idea,', response.data)

    def test_compliance_routes(self):
        """Verify compliance templates return 200 OK."""
        for path in ['/privacy.html', '/terms.html', '/DCL.html', '/Model.html']:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)

    def test_anonymous_rate_limiting(self):
        """Verify that anonymous IP rate limiting caps at 3 roasts per day."""
        # 1st roast: Should succeed (uses fallback response since API keys are empty in test)
        response = self.client.post('/', data={
            'user_input': 'Test startup concept 1',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Substack for ADHD-addled attention spans', response.data)

        # 2nd roast
        response = self.client.post('/', data={
            'user_input': 'Test startup concept 2',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # 3rd roast
        response = self.client.post('/', data={
            'user_input': 'Test startup concept 3',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # 4th roast: Should trigger rate limit warning
        response = self.client.post('/', data={
            'user_input': 'Test startup concept 4',
            'intensity': 'Savage',
            'personality': 'Tech Bro'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Rate Limit Exceeded', response.data)
        self.assertIn(b'3 / 3 Daily Limit', response.data)

if __name__ == '__main__':
    unittest.main()
