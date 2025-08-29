from app import app
from flask_migrate import upgrade

# Runs Alembic migrations inside the Flask app context
with app.app_context():
    upgrade()
