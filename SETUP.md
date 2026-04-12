# Quick Setup Guide

## Step-by-Step Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
python init_db.py
```
This creates the database and adds sample medical camps.

### 3. Train ML Model
```bash
python train_model.py
```
This creates sample training data and trains the disease prediction model.

### 4. Run Application
```bash
python run.py
```

### 5. Access the Application
- **User Interface**: http://localhost:5000
- **Admin Panel**: http://localhost:5000/admin/login
  - Username: `admin`
  - Password: `admin123`

## Testing the Application

1. **Test Symptom Analysis**:
   - Go to http://localhost:5000
   - Enter patient details (name, age, gender)
   - Enter symptoms like: "fever, cough, headache"
   - Click "Analyze Symptoms"
   - View prediction results and download receipt

2. **Test Admin Panel**:
   - Login at http://localhost:5000/admin/login
   - View existing medical camps
   - Add a new medical camp
   - Edit or delete existing camps
   - View recent consultations

3. **Test Receipt Generation**:
   - After analyzing symptoms, you'll be redirected to receipt page
   - Click "Download PDF" to get the digital receipt

## Troubleshooting

- **Import Errors**: Make sure all dependencies are installed
- **Database Errors**: Delete `healthcare_assistant.db` and run `python init_db.py` again
- **Model Errors**: Run `python train_model.py` to regenerate the model
- **Port Conflicts**: Change port in `app.py` or `run.py` if 5000 is in use

## Next Steps

1. **Customize Training Data**: Edit `data/training_data.csv` with your own symptom-disease mappings
2. **Add More Medicines**: Update `data/medicines.json` with additional medicine suggestions
3. **Change Admin Credentials**: Update `config.py` with secure credentials
4. **Deploy**: Configure for production deployment (use proper database, secure admin credentials, etc.)

