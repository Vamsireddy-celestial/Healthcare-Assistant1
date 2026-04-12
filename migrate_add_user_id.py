"""
Migration script to add user_id column to consultations table
"""
from app import app, db
from sqlalchemy import text

def migrate_add_user_id():
    """Add user_id column to consultations table if it doesn't exist"""
    with app.app_context():
        try:
            # Check if column exists by trying to query it
            result = db.session.execute(text("PRAGMA table_info(consultations)"))
            columns = [row[1] for row in result]
            
            if 'user_id' not in columns:
                print("Adding user_id column to consultations table...")
                # Add the user_id column
                db.session.execute(text("""
                    ALTER TABLE consultations 
                    ADD COLUMN user_id INTEGER REFERENCES users(id)
                """))
                db.session.commit()
                print("Success: user_id column added successfully!")
            else:
                print("Info: user_id column already exists in consultations table.")
        except Exception as e:
            print(f"Error during migration: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate_add_user_id()
