# Smart Healthcare Assistant (SHA)

An AI-based Smart Healthcare Assistant that analyzes user symptoms to predict possible diseases and recommends appropriate medical specialization.

## Features

- **Symptom Analysis**: Users can enter multiple symptoms through a user-friendly interface
- **Disease Prediction**: ML-based prediction of possible diseases
- **Medical Specialization Recommendation**: Suggests appropriate doctor specialization
- **Temporary Medicine Suggestions**: Provides safe temporary medicine recommendations
- **Medical Camp Information**: Displays free government medical camp details
- **Digital Receipt**: Generates downloadable consultation receipt with token/OTP
- **Admin Panel**: Manage medical camp information

## Installation

1. **Install Python 3.8 or higher**
   - Make sure Python is installed on your system

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database:**
   ```bash
   python init_db.py
   ```
   This will create the database tables and add sample medical camp data.

4. **Train the ML model:**
   ```bash
   python train_model.py
   ```
   This will create sample training data if it doesn't exist and train the model.
   The model will be saved in the `models/` directory.

5. **Run the application:**
   ```bash
   python run.py
   ```
   Or alternatively:
   ```bash
   python app.py
   ```

6. **Open your browser and navigate to:**
   - Main Application: `http://localhost:5000`
   - Admin Panel: `http://localhost:5000/admin/login`

## Default Admin Credentials

- Username: `admin`
- Password: `admin123`

**Note**: Change these credentials in production!

## Project Structure

```
SHA/
├── app.py                 # Main Flask application
├── run.py                 # Simple startup script
├── models.py              # Database models
├── ml_model.py            # ML model for disease prediction
├── train_model.py         # Script to train ML model
├── init_db.py             # Database initialization
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   ├── index.html         # User interface
│   ├── admin.html         # Admin panel
│   ├── admin_login.html   # Admin login page
│   └── receipt.html       # Receipt view
├── static/                # Static files (CSS, JS)
│   ├── css/
│   │   └── style.css      # Main stylesheet
│   └── js/
│       ├── main.js        # User interface JavaScript
│       └── admin.js        # Admin panel JavaScript
├── data/                  # Data files
│   ├── training_data.csv  # ML training dataset (auto-generated)
│   └── medicines.json     # Medicine dataset
├── models/                # Trained ML models
│   └── disease_predictor.pkl  # Saved model (after training)
└── uploads/               # Generated receipts
```

## Usage Guide

### For Users:
1. Enter your personal details (name, age, gender)
2. Enter your symptoms (separated by commas)
3. Click "Analyze Symptoms" to get:
   - Predicted disease
   - Recommended medical specialization
   - Temporary medicine suggestions
   - Digital consultation receipt with token
4. View available free government medical camps
5. Download your consultation receipt as PDF

### For Administrators:
1. Login at `/admin/login` with admin credentials
2. View recent consultations
3. Add, edit, or delete medical camp information
4. Manage camp details (name, location, date, time, services)

## Technologies Used

- **Backend**: Flask (Python)
- **Database**: SQLite (via Flask-SQLAlchemy)
- **ML Library**: Scikit-learn (Random Forest Classifier)
- **PDF Generation**: ReportLab
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Authentication**: Flask-Login

## Important Notes

⚠️ **Medical Disclaimer**: This system provides advisory predictions only. It does not replace professional medical diagnosis. Users should always consult qualified healthcare professionals for proper diagnosis and treatment.

🔒 **Security**: Change the default admin credentials in `config.py` before deploying to production.

📊 **ML Model**: The model uses a fallback prediction system if not trained. For better accuracy, train the model with your own dataset.

## Troubleshooting

- **Database errors**: Run `python init_db.py` to recreate the database
- **Model not found**: Run `python train_model.py` to train and save the model
- **Port already in use**: Change the port in `app.py` or `run.py`

## License

This project is for educational purposes.

