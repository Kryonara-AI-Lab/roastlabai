# Sentinel's Journal - Security Learnings

## 2026-08-01 - Flask Session SECRET_KEY Hardcoding
**Vulnerability:** The Flask application configuration was hardcoding `SECRET_KEY = 'roastlab_secret_key_change_this_immediately'`.
**Learning:** Developers often placeholder configuration parameters like `SECRET_KEY` during early scaffolding or rapid prototyping with the intention of updating them later. However, these hardcoded values can easily slip into production, exposing the application to cookie-tampering and session-hijacking/forgery.
**Prevention:** Always load secrets dynamically from the environment (`os.environ.get('SECRET_KEY')`) with a secure fallback only explicitly designed for local development. Use robust test mockups to ensure that configurations are successfully customizable per deployment.