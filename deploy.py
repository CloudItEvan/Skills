from flask_migrate import upgrade
from app import create_app, db

app = create_app()

# Run migrations before starting the app
with app.app_context():
    upgrade()
