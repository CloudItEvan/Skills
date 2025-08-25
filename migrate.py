# migrate.py
from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN profile_pic VARCHAR(255);"))
            print("✅ Column 'profile_pic' added successfully!")
    except Exception as e:
        print("⚠️ Migration skipped or failed:", e)
