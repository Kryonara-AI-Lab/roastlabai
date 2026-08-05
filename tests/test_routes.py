import os
import tempfile
import unittest
import json
import sqlite3
from unittest.mock import patch, MagicMock

# Import app modules
from app import create_app, routes

class RoastLabTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary file for the SQLite database
        self.db_fd, self.temp_db_path = tempfile.mkstemp()

        # Override the database path in routes to point to the test database
        self.original_db_path = routes.DB_PATH
        routes.DB_PATH = self.temp_db_path

        # Initialize the test database
        routes.init_db()

        # Configure and create the Flask app
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test_secret_key'
        self.client = self.app.test_client()

    def tearDown(self):
        # Close the file descriptor and remove the temporary database file
        os.close(self.db_fd)
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)

        # Restore original database path
        routes.DB_PATH = self.original_db_path

    def test_database_indexes_exist(self):
        """Verify that our optimized composite indexes are successfully created in the database schema."""
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index'")
        indexes = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()

        self.assertIn('idx_roasts_user_created', indexes)
        self.assertIn('idx_roasts_ip_user_created', indexes)

        # Check that the index definitions are correct
        self.assertTrue('user_id' in indexes['idx_roasts_user_created'])
        self.assertTrue('created_at' in indexes['idx_roasts_user_created'])
        self.assertTrue('ip_address' in indexes['idx_roasts_ip_user_created'])

    def test_index_page_loads(self):
        """Test that the index page loads successfully."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'RoastLab AI', response.data)

    def test_signup_and_login(self):
        """Test signup, auto-login, and login flows."""
        # 1. Sign up
        response = self.client.post('/signup', data={
            'email': 'bolt@speed.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'bolt@speed.com', response.data)

        # Log out
        self.client.get('/logout', follow_redirects=True)

        # 2. Login
        response = self.client.post('/login', data={
            'email': 'bolt@speed.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'bolt@speed.com', response.data)

    @patch('requests.post')
    def test_anonymous_rate_limiting(self, mock_post):
        """Test that anonymous visitors are restricted to exactly 3 roasts per day."""
        # Mock requests.post to return mock JSON
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        "headline": "Slightly too fast",
                        "score": 42,
                        "roast_bullets": ["1", "2", "3", "4", "5"],
                        "brutal_truth": "Truth",
                        "worth_saving": "Saving",
                        "eats_lunch": "Lunch",
                        "one_move": "Move"
                    })
                }
            }]
        }
        mock_post.return_value = mock_response

        # Force no API key so fallback or mock POST runs smoothly (we mocked post anyway)
        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'mock_key'}):
            # First 3 roasts should succeed
            for i in range(3):
                response = self.client.post('/', data={
                    'user_input': f'My Startup Idea {i}',
                    'intensity': 'Savage',
                    'personality': 'Tech Bro'
                })
                self.assertEqual(response.status_code, 200)
                self.assertNotIn(b"Rate Limit Exceeded", response.data)

            # 4th roast should be rate-limited
            response = self.client.post('/', data={
                'user_input': 'The 4th Startup Idea',
                'intensity': 'Savage',
                'personality': 'Tech Bro'
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Rate Limit Exceeded", response.data)

    @patch('requests.post')
    def test_logged_in_rate_limiting(self, mock_post):
        """Test that logged-in users are restricted to exactly 3 roasts per day using range-based optimization."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        "headline": "Slightly too fast",
                        "score": 42,
                        "roast_bullets": ["1", "2", "3", "4", "5"],
                        "brutal_truth": "Truth",
                        "worth_saving": "Saving",
                        "eats_lunch": "Lunch",
                        "one_move": "Move"
                    })
                }
            }]
        }
        mock_post.return_value = mock_response

        # Sign up and log in
        self.client.post('/signup', data={
            'email': 'user@limit.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'mock_key'}):
            # First 3 roasts should succeed
            for i in range(3):
                response = self.client.post('/', data={
                    'user_input': f'My Logged-in Idea {i}',
                    'intensity': 'Savage',
                    'personality': 'Tech Bro'
                })
                self.assertEqual(response.status_code, 200)
                self.assertNotIn(b"Rate Limit Exceeded", response.data)

            # 4th roast should be rate-limited
            response = self.client.post('/', data={
                'user_input': 'The 4th Logged-in Idea',
                'intensity': 'Savage',
                'personality': 'Tech Bro'
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Rate Limit Exceeded", response.data)

    def test_history_ordering(self):
        """Verify that user history loads in descending order of created_at."""
        # Sign up and log in
        self.client.post('/signup', data={
            'email': 'history@test.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        # Get the user ID from the database
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email='history@test.com'")
        user_id = cursor.fetchone()[0]

        # Insert historical roasts with different created_at timestamps (ascending order)
        roast_data_a = json.dumps({
            "headline": "Headline A",
            "score": 10,
            "roast_bullets": ["1", "2", "3", "4", "5"],
            "brutal_truth": "Truth",
            "worth_saving": "Saving",
            "eats_lunch": "Lunch",
            "one_move": "Move"
        })
        roast_data_b = json.dumps({
            "headline": "Headline B",
            "score": 20,
            "roast_bullets": ["1", "2", "3", "4", "5"],
            "brutal_truth": "Truth",
            "worth_saving": "Saving",
            "eats_lunch": "Lunch",
            "one_move": "Move"
        })
        roast_data_c = json.dumps({
            "headline": "Headline C",
            "score": 30,
            "roast_bullets": ["1", "2", "3", "4", "5"],
            "brutal_truth": "Truth",
            "worth_saving": "Saving",
            "eats_lunch": "Lunch",
            "one_move": "Move"
        })

        cursor.execute("""
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (?, '127.0.0.1', 'Idea A', ?, '2026-07-01 10:00:00')
        """, (user_id, roast_data_a))
        cursor.execute("""
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (?, '127.0.0.1', 'Idea B', ?, '2026-07-01 11:00:00')
        """, (user_id, roast_data_b))
        cursor.execute("""
            INSERT INTO roasts (user_id, ip_address, user_input, roast_result, created_at)
            VALUES (?, '127.0.0.1', 'Idea C', ?, '2026-07-01 12:00:00')
        """, (user_id, roast_data_c))
        conn.commit()
        conn.close()

        # Load index page and check history ordering (it should render C first, then B, then A)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        content = response.data.decode('utf-8')
        pos_a = content.find('Headline A')
        pos_b = content.find('Headline B')
        pos_c = content.find('Headline C')

        # Since it is rendered in descending order, C should appear before B, and B before A
        self.assertNotEqual(pos_a, -1)
        self.assertNotEqual(pos_b, -1)
        self.assertNotEqual(pos_c, -1)
        self.assertTrue(pos_c < pos_b < pos_a, f"History not in descending order: C({pos_c}), B({pos_b}), A({pos_a})")

if __name__ == '__main__':
    unittest.main()
