"""
Main Flask Application for Smart Healthcare Assistant
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
from models import db, Consultation, MedicalCamp
from ml_model import predictor
from config import Config
from datetime import datetime
import json
import os
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import io

app = Flask(__name__)
app.config.from_object(Config)


def load_available_symptoms():
    """Load unique symptoms from training data for dropdown."""
    # Use path relative to this file so it works regardless of working directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    symptoms_file = os.path.join(base_dir, 'data', 'training_data.csv')
    symptoms_set = set()

    if os.path.exists(symptoms_file):
        try:
            with open(symptoms_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    raw = row.get('symptoms', '')
                    # Strip quotes if CSV left them on (e.g. "fever,cough" -> fever,cough)
                    raw = str(raw).strip().strip('"')
                    for s in raw.split(','):
                        s_clean = s.strip().strip('"')
                        if s_clean:
                            symptoms_set.add(s_clean)
        except Exception:
            # Fail silently – UI will fall back to manual entry if needed
            pass

    return sorted(symptoms_set)


AVAILABLE_SYMPTOMS = load_available_symptoms()

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

# User class for admin login
class AdminUser(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return AdminUser(user_id)

# Routes
@app.route('/')
def index():
    """Main user interface"""
    return render_template('index.html', symptoms=AVAILABLE_SYMPTOMS)


@app.route('/api/symptoms', methods=['GET'])
def get_symptoms():
    """Return list of available symptoms (from training data) for dropdown."""
    # Reload from disk so updates to CSV are picked up without restart
    symptoms = load_available_symptoms()
    return jsonify({'success': True, 'symptoms': symptoms})

@app.route('/api/predict', methods=['POST'])
def predict_disease():
    """API endpoint for disease prediction"""
    try:
        data = request.json
        symptoms = data.get('symptoms', [])
        patient_name = data.get('patient_name', '')
        age = data.get('age', 0)
        gender = data.get('gender', '')
        
        if not symptoms:
            return jsonify({'error': 'Please enter at least one symptom'}), 400
        
        # Predict disease
        predicted_disease, confidence, specialization = predictor.predict(symptoms)
        
        # Generate numeric token (priority for seniors: smaller numbers)
        try:
            age_int = int(age)
        except (TypeError, ValueError):
            age_int = 0

        # Seniors (>=60) get tokens in 000000-499999, others in 500000-999999
        if age_int >= 60:
            token = Consultation.generate_token(0, 499999)
        else:
            token = Consultation.generate_token(500000, 999999)
        
        # Save consultation
        consultation = Consultation(
            patient_name=patient_name,
            age=age,
            gender=gender,
            symptoms=', '.join(symptoms),
            predicted_disease=predicted_disease,
            recommended_specialization=specialization,
            token=token
        )
        db.session.add(consultation)
        db.session.commit()
        
        # Get medicine suggestions based on both disease and specialization
        medicines = get_medicine_suggestions(predicted_disease, specialization)
        
        return jsonify({
            'success': True,
            'predicted_disease': predicted_disease,
            'confidence': round(confidence * 100, 2),
            'recommended_specialization': specialization,
            'specialization': specialization,  # Keep for backward compatibility
            'token': token,
            'consultation_id': consultation.id,
            'medicines': medicines
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/camps', methods=['GET'])
def get_medical_camps():
    """Get all medical camps"""
    try:
        camps = MedicalCamp.query.order_by(MedicalCamp.date.asc()).all()
        return jsonify({
            'success': True,
            'camps': [camp.to_dict() for camp in camps]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/receipt/<int:consultation_id>', methods=['GET'])
def get_receipt(consultation_id):
    """Get consultation receipt"""
    try:
        consultation = Consultation.query.get_or_404(consultation_id)
        return jsonify({
            'success': True,
            'receipt': consultation.to_dict()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/receipt/<int:consultation_id>')
def view_receipt(consultation_id):
    """View receipt page"""
    consultation = Consultation.query.get_or_404(consultation_id)
    # Get medicine suggestions based on consultation's disease and specialization
    medicines = get_medicine_suggestions(
        consultation.predicted_disease,
        consultation.recommended_specialization
    )
    return render_template('receipt.html', consultation=consultation, medicines=medicines)

@app.route('/receipt/<int:consultation_id>/download')
def download_receipt(consultation_id):
    """Download receipt as PDF"""
    consultation = Consultation.query.get_or_404(consultation_id)
    # Get medicine suggestions for the PDF
    medicines = get_medicine_suggestions(
        consultation.predicted_disease,
        consultation.recommended_specialization
    )
    
    # Create PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, "Digital Consultation Receipt")
    
    # Line
    p.line(50, height - 60, width - 50, height - 60)
    
    y = height - 100
    
    # Patient Details
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Patient Details:")
    y -= 25
    
    p.setFont("Helvetica", 12)
    details = [
        f"Name: {consultation.patient_name}",
        f"Age: {consultation.age}",
        f"Gender: {consultation.gender}",
        f"Token Number: {consultation.token}",
        f"Date & Time: {consultation.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    ]
    
    for detail in details:
        p.drawString(70, y, detail)
        y -= 20
    
    y -= 10
    
    # Consultation Details
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Consultation Details:")
    y -= 25
    
    p.setFont("Helvetica", 12)
    # Handle long symptoms text by wrapping
    symptoms_text = f"Symptoms: {consultation.symptoms}"
    if len(symptoms_text) > 70:
        p.drawString(70, y, symptoms_text[:70])
        y -= 20
        p.drawString(70, y, symptoms_text[70:])
    else:
        p.drawString(70, y, symptoms_text)
    y -= 20
    p.drawString(70, y, f"Predicted Disease: {consultation.predicted_disease}")
    y -= 20
    p.drawString(70, y, f"Recommended Specialization: {consultation.recommended_specialization}")
    
    y -= 30
    
    # Medicine Suggestions
    if medicines:
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, y, "Temporary Medicine Suggestions:")
        y -= 20
        
        p.setFont("Helvetica-Oblique", 10)
        p.drawString(50, y, "Note: These are temporary suggestions for basic relief only.")
        y -= 15
        p.drawString(50, y, "Please consult a healthcare professional for proper diagnosis and treatment.")
        y -= 20
        
        p.setFont("Helvetica-Bold", 11)
        # Table headers
        p.drawString(50, y, "Medicine Name")
        p.drawString(200, y, "Dosage")
        p.drawString(320, y, "Frequency")
        p.drawString(450, y, "Duration")
        y -= 20
        
        p.line(50, y, width - 50, y)
        y -= 15
        
        p.setFont("Helvetica", 10)
        for medicine in medicines:
            # Check if we need a new page
            if y < 100:
                p.showPage()
                y = height - 50
                p.setFont("Helvetica", 10)
            
            name = medicine.get('name', 'N/A')
            dosage = medicine.get('dosage', 'N/A')
            frequency = medicine.get('frequency', 'N/A')
            duration = medicine.get('duration', 'N/A')
            
            # Wrap long text if needed
            p.drawString(50, y, name[:30] if len(name) <= 30 else name[:27] + "...")
            p.drawString(200, y, dosage[:18] if len(dosage) <= 18 else dosage[:15] + "...")
            p.drawString(320, y, frequency[:22] if len(frequency) <= 22 else frequency[:19] + "...")
            p.drawString(450, y, duration[:18] if len(duration) <= 18 else duration[:15] + "...")
            y -= 18
        
        y -= 10
    
    # Disclaimer
    y -= 10
    if y < 80:
        p.showPage()
        y = height - 50
    
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, y, "Note: This is an advisory prediction. Please consult a healthcare professional for proper diagnosis.")
    y -= 15
    p.drawString(50, y, "This receipt is for reference during your medical visit.")
    
    p.save()
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'consultation_receipt_{consultation.token}.pdf'
    )

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == app.config['ADMIN_USERNAME'] and password == app.config['ADMIN_PASSWORD']:
            user = AdminUser(username)
            login_user(user)
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    """Admin logout"""
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_panel():
    """Admin panel"""
    camps = MedicalCamp.query.order_by(MedicalCamp.date.asc()).all()
    consultations = Consultation.query.order_by(Consultation.created_at.desc()).limit(50).all()
    return render_template('admin.html', camps=camps, consultations=consultations)

@app.route('/admin/camps/<int:camp_id>', methods=['GET'])
@login_required
def get_camp(camp_id):
    """Get a single medical camp"""
    camp = MedicalCamp.query.get_or_404(camp_id)
    return jsonify({'success': True, 'camp': camp.to_dict()})

@app.route('/admin/camps', methods=['GET', 'POST'])
@login_required
def manage_camps():
    """Manage medical camps"""
    if request.method == 'POST':
        action = request.json.get('action')
        
        if action == 'add':
            camp = MedicalCamp(
                camp_name=request.json['camp_name'],
                location=request.json['location'],
                date=datetime.strptime(request.json['date'], '%Y-%m-%d').date(),
                time=request.json['time'],
                services_offered=request.json['services_offered'],
                contact_info=request.json.get('contact_info', '')
            )
            db.session.add(camp)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Camp added successfully'})
        
        elif action == 'update':
            camp = MedicalCamp.query.get(request.json['id'])
            if camp:
                camp.camp_name = request.json['camp_name']
                camp.location = request.json['location']
                camp.date = datetime.strptime(request.json['date'], '%Y-%m-%d').date()
                camp.time = request.json['time']
                camp.services_offered = request.json['services_offered']
                camp.contact_info = request.json.get('contact_info', '')
                camp.updated_at = datetime.utcnow()
                db.session.commit()
                return jsonify({'success': True, 'message': 'Camp updated successfully'})
            return jsonify({'success': False, 'message': 'Camp not found'}), 404
        
        elif action == 'delete':
            camp = MedicalCamp.query.get(request.json['id'])
            if camp:
                db.session.delete(camp)
                db.session.commit()
                return jsonify({'success': True, 'message': 'Camp deleted successfully'})
            return jsonify({'success': False, 'message': 'Camp not found'}), 404
    
    return jsonify({'error': 'Invalid request'}), 400

def get_medicine_suggestions(disease, specialization=None):
    """Get medicine suggestions based on predicted disease and specialization"""
    # Load medicines data
    medicines_file = 'data/medicines.json'
    
    if os.path.exists(medicines_file):
        with open(medicines_file, 'r', encoding='utf-8') as f:
            medicines_data = json.load(f)
    else:
        # Default medicines data
        medicines_data = {
            'Common Cold': [
                {'name': 'Paracetamol', 'dosage': '500mg', 'frequency': 'Every 6-8 hours', 'duration': '3-5 days'},
                {'name': 'Vitamin C', 'dosage': '500mg', 'frequency': 'Once daily', 'duration': '5-7 days'}
            ],
            'Flu': [
                {'name': 'Paracetamol', 'dosage': '500mg', 'frequency': 'Every 6-8 hours', 'duration': '3-5 days'},
                {'name': 'Rest and Hydration', 'dosage': 'N/A', 'frequency': 'As needed', 'duration': 'Until recovery'}
            ],
            'Migraine': [
                {'name': 'Ibuprofen', 'dosage': '400mg', 'frequency': 'Every 6-8 hours', 'duration': 'As needed'},
                {'name': 'Rest in dark room', 'dosage': 'N/A', 'frequency': 'As needed', 'duration': 'Until relief'}
            ],
            'Skin Allergy': [
                {'name': 'Antihistamine (Cetirizine)', 'dosage': '10mg', 'frequency': 'Once daily', 'duration': '3-5 days'},
                {'name': 'Topical Calamine Lotion', 'dosage': 'Apply thin layer', 'frequency': '2-3 times daily', 'duration': 'Until rash clears'}
            ],
            'Gastroenteritis': [
                {'name': 'Oral Rehydration Solution', 'dosage': 'As per instructions', 'frequency': 'Frequently', 'duration': 'Until recovery'},
                {'name': 'Probiotics', 'dosage': 'As per product', 'frequency': 'Once daily', 'duration': '5-7 days'}
            ]
        }
    
    # Specialization-based medicine mapping for better accuracy
    specialization_medicines = {
        'General Physician': {
            'Common Cold': medicines_data.get('Common Cold', []),
            'Flu': medicines_data.get('Flu', []),
            'Fever': [
                {'name': 'Paracetamol', 'dosage': '500mg', 'frequency': 'Every 6-8 hours', 'duration': '3-5 days'},
                {'name': 'Adequate rest and fluids', 'dosage': 'N/A', 'frequency': 'As needed', 'duration': 'Until recovery'}
            ]
        },
        'Neurologist': {
            'Migraine': medicines_data.get('Migraine', []),
            'Headache': medicines_data.get('Headache', []),
            'default': [
                {'name': 'Consult Neurologist for proper diagnosis', 'dosage': 'N/A', 'frequency': 'N/A', 'duration': 'N/A'},
                {'name': 'Avoid triggers (stress, bright lights)', 'dosage': 'N/A', 'frequency': 'N/A', 'duration': 'N/A'}
            ]
        },
        'Cardiologist': {
            'Cardiac Issue': medicines_data.get('Cardiac Issue', []),
            'default': [
                {'name': 'Seek immediate medical attention', 'dosage': 'N/A', 'frequency': 'N/A', 'duration': 'N/A'},
                {'name': 'Do not self-medicate cardiac conditions', 'dosage': 'N/A', 'frequency': 'N/A', 'duration': 'N/A'}
            ]
        },
        'Dermatologist': {
            'Skin Allergy': medicines_data.get('Skin Allergy', []),
            'default': [
                {'name': 'Antihistamine (Cetirizine)', 'dosage': '10mg', 'frequency': 'Once daily', 'duration': '3-5 days'},
                {'name': 'Topical Calamine Lotion', 'dosage': 'Apply thin layer', 'frequency': '2-3 times daily', 'duration': 'Until relief'}
            ]
        },
        'Gastroenterologist': {
            'Gastroenteritis': medicines_data.get('Gastroenteritis', []),
            'default': [
                {'name': 'Oral Rehydration Solution', 'dosage': 'As per instructions', 'frequency': 'Frequently', 'duration': 'Until recovery'},
                {'name': 'Probiotics', 'dosage': 'As per product', 'frequency': 'Once daily', 'duration': '5-7 days'}
            ]
        },
        'Rheumatologist': {
            'Arthritis': medicines_data.get('Arthritis', []),
            'default': [
                {'name': 'Ibuprofen', 'dosage': '400mg', 'frequency': 'Every 8 hours', 'duration': 'As needed'},
                {'name': 'Warm compress to affected area', 'dosage': 'N/A', 'frequency': '2-3 times daily', 'duration': 'Until relief'}
            ]
        },
        'Pulmonologist': {
            'Asthma': medicines_data.get('Asthma', []),
            'default': [
                {'name': 'Inhaler (if previously prescribed)', 'dosage': 'As per prescription', 'frequency': 'As needed', 'duration': 'As per doctor'},
                {'name': 'Avoid triggers and allergens', 'dosage': 'N/A', 'frequency': 'Always', 'duration': 'Ongoing'}
            ]
        },
        'Ophthalmologist': {
            'Conjunctivitis': medicines_data.get('Conjunctivitis', []),
            'default': [
                {'name': 'Antibiotic Eye Drops (as prescribed)', 'dosage': 'As prescribed', 'frequency': '2-3 times daily', 'duration': '5-7 days'},
                {'name': 'Warm compress', 'dosage': 'N/A', 'frequency': '2-3 times daily', 'duration': 'Until relief'}
            ]
        },
        'ENT Specialist': {
            'Ear Infection': medicines_data.get('Ear Infection', []),
            'Throat Infection': medicines_data.get('Throat Infection', []),
            'default': [
                {'name': 'Warm saline gargle', 'dosage': 'N/A', 'frequency': '3-4 times daily', 'duration': 'Until relief'},
                {'name': 'Paracetamol for pain', 'dosage': '500mg', 'frequency': 'Every 6-8 hours', 'duration': '3-5 days'}
            ]
        },
        'Endocrinologist': {
            'Anemia': medicines_data.get('Anemia', []),
            'default': [
                {'name': 'Consult Endocrinologist for proper diagnosis', 'dosage': 'N/A', 'frequency': 'N/A', 'duration': 'N/A'},
                {'name': 'Do not self-medicate hormonal/metabolic conditions', 'dosage': 'N/A', 'frequency': 'N/A', 'duration': 'N/A'}
            ]
        }
    }
    
    # Get suggestions for disease - improved matching with specialization consideration
    disease_lower = disease.lower().strip()
    specialization_lower = specialization.lower().strip() if specialization else ''
    suggestions = []
    
    # First, try to get medicines based on specialization (more accurate)
    if specialization and specialization in specialization_medicines:
        spec_meds = specialization_medicines[specialization]
        # Try exact disease match within specialization
        if disease in spec_meds:
            suggestions = spec_meds[disease]
        # Try partial match within specialization
        elif any(d.lower() in disease_lower or disease_lower in d.lower() for d in spec_meds.keys() if d != 'default'):
            for key in spec_meds.keys():
                if key != 'default' and (key.lower() in disease_lower or disease_lower in key.lower()):
                    suggestions = spec_meds[key]
                    break
    
    # If not found by specialization, try disease-based matching
    if not suggestions:
        # First try exact match in general medicines data
        if disease in medicines_data:
            suggestions = medicines_data[disease]
        else:
            # Try partial matching with keywords
            disease_keywords = disease_lower.split()
            
            # Check each medicine category
            best_match = None
            best_score = 0
            
            for key, meds in medicines_data.items():
                key_lower = key.lower()
                score = 0
                
                # Check if any keyword matches
                for keyword in disease_keywords:
                    if keyword in key_lower or key_lower in disease_lower:
                        score += 1
                
                # Also check if key is in disease or vice versa
                if key_lower in disease_lower or disease_lower in key_lower:
                    score += 2
                
                if score > best_score:
                    best_score = score
                    best_match = meds
            
            if best_match and best_score > 0:
                suggestions = best_match
    
    # If still not found, try specialization default
    if not suggestions and specialization and specialization in specialization_medicines:
        spec_meds = specialization_medicines[specialization]
        if 'default' in spec_meds:
            suggestions = spec_meds['default']
    
    # Default suggestions if still not found
    if not suggestions:
        # Provide general suggestions based on common symptoms
        if any(word in disease_lower for word in ['fever', 'cold', 'flu', 'cough']):
            suggestions = [
                {'name': 'Paracetamol', 'dosage': '500mg', 'frequency': 'Every 6-8 hours', 'duration': '3-5 days'},
                {'name': 'Rest and Hydration', 'dosage': 'N/A', 'frequency': 'As needed', 'duration': 'Until recovery'}
            ]
        elif any(word in disease_lower for word in ['headache', 'migraine', 'pain']):
            suggestions = [
                {'name': 'Paracetamol or Ibuprofen', 'dosage': '500mg / 400mg', 'frequency': 'Every 6-8 hours', 'duration': 'As needed'},
                {'name': 'Rest', 'dosage': 'N/A', 'frequency': 'As needed', 'duration': 'Until relief'}
            ]
        elif any(word in disease_lower for word in ['stomach', 'gastro', 'nausea', 'vomiting']):
            suggestions = [
                {'name': 'Oral Rehydration Solution', 'dosage': 'As per instructions', 'frequency': 'Frequently', 'duration': 'Until recovery'},
                {'name': 'Avoid solid foods initially', 'dosage': 'N/A', 'frequency': 'N/A', 'duration': 'Until symptoms improve'}
            ]
        else:
            suggestions = [
                {'name': 'Consult a Healthcare Professional', 'dosage': 'N/A', 'frequency': 'N/A', 'duration': 'N/A'},
                {'name': 'Rest and maintain hydration', 'dosage': 'N/A', 'frequency': 'As needed', 'duration': 'Until consultation'}
            ]
    
    return suggestions

if __name__ == '__main__':
    # Create uploads directory
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)

