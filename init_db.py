"""
Initialize the database with tables
"""
from app import app, db
from models import Consultation, MedicalCamp, User
from datetime import datetime, date

def init_database():
    """Initialize database and create sample data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Check if medical camps already exist
        if MedicalCamp.query.count() == 0:
            # Add sample medical camps
            sample_camps = [
                MedicalCamp(
                    camp_name="Free Health Checkup Camp",
                    location="City Hospital, Main Street, Downtown",
                    date=date(2024, 12, 25),
                    time="9:00 AM - 5:00 PM",
                    services_offered="General checkup, Blood pressure, Blood sugar, BMI measurement",
                    contact_info="Phone: 123-456-7890"
                ),
                MedicalCamp(
                    camp_name="Rural Health Awareness Camp",
                    location="Community Center, Village Road",
                    date=date(2024, 12, 30),
                    time="10:00 AM - 4:00 PM",
                    services_offered="Free consultation, Basic medicines, Health awareness session",
                    contact_info="Phone: 987-654-3210"
                ),
                MedicalCamp(
                    camp_name="Cardiac Health Camp",
                    location="Heart Care Center, Medical District",
                    date=date(2025, 1, 5),
                    time="8:00 AM - 6:00 PM",
                    services_offered="ECG, Blood pressure, Cardiac consultation",
                    contact_info="Phone: 555-123-4567"
                )
            ]
            
            for camp in sample_camps:
                db.session.add(camp)
            
            db.session.commit()
            print("Sample medical camps added!")
        else:
            print("Medical camps already exist in database.")
        
        print("Database initialization completed!")

if __name__ == '__main__':
    init_database()

