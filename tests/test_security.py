import os
import unittest
from unittest.mock import patch
from app import create_app

class SecurityTestCase(unittest.TestCase):
    def test_secret_key_from_env(self):
        """Verify that SECRET_KEY is loaded from the environment when defined."""
        with patch.dict(os.environ, {"SECRET_KEY": "super_secure_env_secret_key"}):
            # Temporarily prevent load_dotenv from overwriting our patched environment if a local .env is present
            with patch("app.load_dotenv") as mock_load:
                app = create_app()
                self.assertEqual(app.config["SECRET_KEY"], "super_secure_env_secret_key")

    def test_secret_key_fallback_default(self):
        """Verify that SECRET_KEY falls back to the default value when not defined in the environment."""
        with patch.dict(os.environ, {}):
            # Pop SECRET_KEY if it exists in the active environment
            os.environ.pop("SECRET_KEY", None)
            with patch("app.load_dotenv") as mock_load:
                app = create_app()
                self.assertEqual(app.config["SECRET_KEY"], "roastlab_default_dev_secret_key_change_in_production")

    def test_app_basic_routes(self):
        """Verify basic application routes load successfully under testing client."""
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as client:
            response = client.get("/")
            self.assertEqual(response.status_code, 200)

            response = client.get("/login")
            self.assertEqual(response.status_code, 200)

            response = client.get("/signup")
            self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()