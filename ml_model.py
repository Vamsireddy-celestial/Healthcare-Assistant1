"""
Machine Learning Model for Disease Prediction
"""
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
import os

class DiseasePredictor:
    """ML model for predicting diseases based on symptoms"""
    
    def __init__(self, model_path='models/disease_predictor.pkl'):
        self.model_path = model_path
        self.model = None
        self.mlb_symptoms = None
        self.mlb_diseases = None
        self.specialization_map = {}
        # Symptom synonym mapping for better matching
        self.symptom_synonyms = {
            'fever': ['fever', 'high fever', 'temperature', 'pyrexia'],
            'cough': ['cough', 'coughing', 'dry cough', 'productive cough'],
            'headache': ['headache', 'head pain', 'head ache', 'cephalgia'],
            'body ache': ['body ache', 'body pain', 'muscle ache', 'myalgia', 'muscle pain'],
            'sore throat': ['sore throat', 'throat pain', 'throat soreness', 'pharyngitis'],
            'runny nose': ['runny nose', 'nasal discharge', 'rhinorrhea', 'running nose'],
            'sneezing': ['sneezing', 'sneeze'],
            'congestion': ['congestion', 'nasal congestion', 'stuffy nose', 'blocked nose'],
            'nausea': ['nausea', 'nauseous', 'feeling sick'],
            'vomiting': ['vomiting', 'vomit', 'throwing up', 'emesis'],
            'diarrhea': ['diarrhea', 'diarrhoea', 'loose stools', 'loose motion'],
            'stomach pain': ['stomach pain', 'abdominal pain', 'belly pain', 'stomach ache', 'stomach cramps', 'abdominal cramps'],
            'rash': ['rash', 'skin rash', 'eruption'],
            'itching': ['itching', 'itch', 'itchy', 'pruritus'],
            'chest pain': ['chest pain', 'chest discomfort', 'chest pressure'],
            'shortness of breath': ['shortness of breath', 'breathing difficulty', 'dyspnea', 'breathlessness', 'difficulty breathing'],
            'wheezing': ['wheezing', 'wheeze'],
            'joint pain': ['joint pain', 'arthralgia', 'joint ache'],
            'fatigue': ['fatigue', 'tiredness', 'exhaustion', 'weakness', 'feeling tired'],
            'dizziness': ['dizziness', 'dizzy', 'vertigo', 'lightheadedness'],
            'eye pain': ['eye pain', 'ocular pain'],
            'eye redness': ['eye redness', 'red eyes', 'pink eye', 'conjunctival redness'],
            'ear pain': ['ear pain', 'earache', 'otalgia', 'ear ache'],
            'hearing loss': ['hearing loss', 'hearing difficulty', 'deafness'],
            'throat pain': ['throat pain', 'sore throat', 'pharyngeal pain'],
            'difficulty swallowing': ['difficulty swallowing', 'dysphagia', 'trouble swallowing'],
        }
        self.load_model()
    
    def load_model(self):
        """Load pre-trained model if exists"""
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                self.model = data['model']
                self.mlb_symptoms = data['mlb_symptoms']
                self.mlb_diseases = data['mlb_diseases']
                self.specialization_map = data['specialization_map']
        else:
            # Initialize with default structure
            self.model = None
            self.mlb_symptoms = MultiLabelBinarizer()
            self.mlb_diseases = MultiLabelBinarizer()
            self.specialization_map = {}
    
    def train(self, data_path='data/training_data.csv'):
        """Train the model on dataset"""
        if not os.path.exists(data_path):
            # Create sample training data
            self._create_sample_data(data_path)
        
        # Load data
        df = pd.read_csv(data_path)
        
        # Prepare features (symptoms) and labels (diseases)
        symptoms_list = df['symptoms'].apply(lambda x: [s.strip() for s in str(x).split(',')])
        diseases_list = df['disease'].apply(lambda x: [d.strip() for d in str(x).split(',')])
        
        # Encode symptoms
        X = self.mlb_symptoms.fit_transform(symptoms_list)
        
        # Encode diseases (take first disease if multiple)
        diseases_single = diseases_list.apply(lambda x: x[0] if x else 'Unknown')
        y = diseases_single.values
        
        # Train model
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Use better parameters for improved accuracy
        self.model = RandomForestClassifier(
            n_estimators=200,  # More trees for better accuracy
            random_state=42,
            max_depth=30,  # Deeper trees
            min_samples_split=2,
            min_samples_leaf=1,
            class_weight='balanced'  # Handle class imbalance
        )
        self.model.fit(X_train, y_train)
        
        # Create specialization mapping
        self._create_specialization_map(df)
        
        # Save model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'mlb_symptoms': self.mlb_symptoms,
                'mlb_diseases': self.mlb_diseases,
                'specialization_map': self.specialization_map
            }, f)
        
        print(f"Model trained and saved to {self.model_path}")
        print(f"Accuracy: {self.model.score(X_test, y_test):.2%}")
    
    def _normalize_symptoms(self, symptoms):
        """
        Normalize and map symptoms to standard forms using synonyms
        
        Args:
            symptoms: List of symptom strings
        
        Returns:
            List of normalized symptom strings
        """
        normalized = []
        for symptom in symptoms:
            symptom_lower = symptom.lower().strip()
            # Try to find matching synonym group
            matched = False
            for standard, synonyms in self.symptom_synonyms.items():
                # Check if symptom matches any synonym (exact or contains)
                for syn in synonyms:
                    if symptom_lower == syn or syn in symptom_lower or symptom_lower in syn:
                        normalized.append(standard)
                        matched = True
                        break
                if matched:
                    break
            
            # If no synonym match, use original (normalized)
            if not matched:
                normalized.append(symptom_lower)
        
        return normalized
    
    def predict(self, symptoms):
        """
        Predict disease from symptoms
        
        Args:
            symptoms: List of symptom strings
        
        Returns:
            tuple: (predicted_disease, confidence, specialization)
        """
        if self.model is None:
            return self._fallback_predict(symptoms)
        
        # Normalize symptoms with synonym mapping
        symptoms_normalized = self._normalize_symptoms(symptoms)
        
        try:
            # First, try with normalized symptoms
            symptoms_encoded = self.mlb_symptoms.transform([symptoms_normalized])
            
            # Predict
            prediction = self.model.predict(symptoms_encoded)[0]
            probabilities = self.model.predict_proba(symptoms_encoded)[0]
            confidence = max(probabilities)
            
            # If confidence is too low, try fallback
            if confidence < 0.3:
                # Also try with original symptoms before fallback
                try:
                    symptoms_original = [s.lower().strip() for s in symptoms]
                    symptoms_encoded_orig = self.mlb_symptoms.transform([symptoms_original])
                    prediction_orig = self.model.predict(symptoms_encoded_orig)[0]
                    probabilities_orig = self.model.predict_proba(symptoms_encoded_orig)[0]
                    confidence_orig = max(probabilities_orig)
                    
                    # Use original if it has better confidence
                    if confidence_orig > confidence:
                        prediction = prediction_orig
                        confidence = confidence_orig
                except:
                    pass
                
                # If still low, use rule-based fallback
                if confidence < 0.3:
                    return self._fallback_predict(symptoms)
            
            # Get specialization
            specialization = self.specialization_map.get(prediction, 'General Physician')
            
            return prediction, confidence, specialization
        except Exception as e:
            # If encoding fails (new symptoms not in training), try fallback
            print(f"Prediction error: {e}, using fallback")
            return self._fallback_predict(symptoms)
    
    def _fallback_predict(self, symptoms):
        """Fallback prediction when model is not trained or confidence is low"""
        # Normalize symptoms first using synonym mapping
        symptoms_normalized = self._normalize_symptoms(symptoms)
        symptoms_lower = [s.lower().strip() for s in symptoms]
        symptoms_str = ' '.join(symptoms_normalized)
        
        # Enhanced symptom-disease mapping with priority
        disease_rules = [
            # Cardiac issues (high priority)
            (['chest pain', 'shortness of breath', 'heart palpitations', 'arm pain', 'arm numbness'], 'Cardiac Issue', 'Cardiologist'),
            # Respiratory issues
            (['wheezing', 'asthma', 'breathing difficulty'], 'Asthma', 'Pulmonologist'),
            (['cough', 'wheezing', 'chest tightness'], 'Asthma', 'Pulmonologist'),
            # Infections
            (['fever', 'cough', 'sore throat', 'runny nose', 'body ache', 'chills'], 'Flu', 'General Physician'),
            (['fever', 'cough', 'headache', 'body ache'], 'Common Cold', 'General Physician'),
            (['cough', 'sneezing', 'runny nose', 'congestion'], 'Common Cold', 'General Physician'),
            # Neurological
            (['severe headache', 'migraine', 'throbbing headache', 'sensitivity to light', 'sensitivity to sound'], 'Migraine', 'Neurologist'),
            (['headache', 'nausea', 'dizziness', 'vomiting'], 'Migraine', 'Neurologist'),
            # Skin issues
            (['rash', 'itching', 'hives', 'redness', 'swelling', 'skin irritation'], 'Skin Allergy', 'Dermatologist'),
            # Gastrointestinal
            (['nausea', 'vomiting', 'diarrhea', 'stomach pain', 'abdominal pain', 'stomach cramps'], 'Gastroenteritis', 'Gastroenterologist'),
            # Joint/Musculoskeletal
            (['joint pain', 'swelling', 'stiffness', 'arthritis'], 'Arthritis', 'Rheumatologist'),
            # Blood/Anemia
            (['fatigue', 'weakness', 'pale skin', 'dizziness', 'shortness of breath'], 'Anemia', 'General Physician'),
            # Eye issues
            (['eye pain', 'redness', 'blurred vision', 'discharge', 'pink eye', 'conjunctivitis'], 'Conjunctivitis', 'Ophthalmologist'),
            # Ear issues
            (['ear pain', 'earache', 'hearing loss', 'discharge', 'ear infection'], 'Ear Infection', 'ENT Specialist'),
            # Throat issues
            (['throat pain', 'sore throat', 'difficulty swallowing', 'hoarseness', 'strep throat', 'tonsillitis'], 'Throat Infection', 'ENT Specialist'),
        ]
        
        # Score each disease based on matching symptoms
        disease_scores = {}
        for symptom_list, disease, specialization in disease_rules:
            score = 0
            for symptom in symptoms_lower:
                for pattern in symptom_list:
                    if pattern in symptom or symptom in pattern:
                        score += 1
            if score > 0:
                if disease not in disease_scores or score > disease_scores[disease][0]:
                    disease_scores[disease] = (score, specialization)
        
        # Return the disease with highest score
        if disease_scores:
            best_disease = max(disease_scores.items(), key=lambda x: x[1][0])
            disease_name = best_disease[0]
            specialization = best_disease[1][1]
            # Calculate confidence based on score
            max_possible_score = len(symptoms) * 2  # Rough estimate
            confidence = min(0.75, 0.5 + (best_disease[1][0] / max_possible_score))
            return disease_name, confidence, specialization
        
        return 'General Health Concern', 0.5, 'General Physician'
    
    def _create_specialization_map(self, df):
        """Create mapping from disease to specialization"""
        # Default specialization mapping
        default_map = {
            'Common Cold': 'General Physician',
            'Flu': 'General Physician',
            'Fever': 'General Physician',
            'Migraine': 'Neurologist',
            'Headache': 'Neurologist',
            'Cardiac': 'Cardiologist',
            'Heart': 'Cardiologist',
            'Skin': 'Dermatologist',
            'Rash': 'Dermatologist',
            'Allergy': 'Dermatologist',
            'Gastro': 'Gastroenterologist',
            'Stomach': 'Gastroenterologist',
            'Arthritis': 'Rheumatologist',
            'Joint': 'Rheumatologist',
            'Diabetes': 'Endocrinologist',
            'Thyroid': 'Endocrinologist',
            'Asthma': 'Pulmonologist',
            'Lung': 'Pulmonologist',
            'Eye': 'Ophthalmologist',
            'Vision': 'Ophthalmologist',
            'Ear': 'ENT Specialist',
            'Nose': 'ENT Specialist',
            'Throat': 'ENT Specialist'
        }
        
        # Extract unique diseases from dataset
        diseases = set()
        for disease_list in df['disease']:
            diseases.update([d.strip() for d in str(disease_list).split(',')])
        
        # Map diseases to specializations
        for disease in diseases:
            disease_lower = disease.lower()
            specialization = 'General Physician'
            
            for key, spec in default_map.items():
                if key.lower() in disease_lower:
                    specialization = spec
                    break
            
            self.specialization_map[disease] = specialization
    
    def _create_sample_data(self, data_path):
        """Create sample training data if file doesn't exist"""
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        
        # Comprehensive training data matching training_data.csv
        sample_data = {
            'symptoms': [
                'fever,cough,headache,body ache',
                'fever,cough,sore throat,runny nose',
                'fever,cough,headache',
                'cough,sneezing,runny nose',
                'fever,chills,body ache',
                'fever,cough,fatigue',
                'sore throat,fever,cough',
                'headache,nausea,dizziness',
                'severe headache,sensitivity to light',
                'headache,vomiting',
                'throbbing headache',
                'chest pain,shortness of breath,fatigue',
                'chest pain,heart palpitations',
                'chest pain,shortness of breath',
                'chest pain,arm pain',
                'rash,itching,redness',
                'skin rash,itching',
                'redness,itching,swelling',
                'hives,itching',
                'nausea,vomiting,stomach pain',
                'diarrhea,nausea,vomiting',
                'stomach pain,nausea',
                'vomiting,diarrhea,abdominal pain',
                'joint pain,swelling,stiffness',
                'joint pain,morning stiffness',
                'joint swelling,pain',
                'knee pain,swelling',
                'fatigue,weakness,pale skin',
                'fatigue,dizziness,weakness',
                'pale skin,fatigue',
                'weakness,shortness of breath',
                'cough,wheezing,shortness of breath',
                'wheezing,chest tightness',
                'shortness of breath,cough',
                'breathing difficulty,wheezing',
                'eye pain,redness,blurred vision',
                'red eyes,itching,discharge',
                'eye redness,watering',
                'eye irritation,redness',
                'ear pain,hearing loss,discharge',
                'ear pain,fever',
                'earache,discharge',
                'ear pain,hearing difficulty',
                'throat pain,difficulty swallowing,hoarseness',
                'sore throat,fever',
                'throat pain,swollen glands',
                'difficulty swallowing,sore throat',
                'fever,body ache,chills',
                'fever,cough,headache,muscle pain',
                'runny nose,sneezing,congestion',
                'cough,headache,body ache',
                'fever,headache,body ache',
                'nausea,vomiting,diarrhea,fever',
                'abdominal pain,cramps,diarrhea',
                'stomach cramps,nausea',
                'chest pain,shortness of breath,dizziness',
                'chest discomfort,shortness of breath',
                'heart racing,chest pain',
                'headache,neck pain,stiffness',
                'headache,eye pain',
                'severe headache,nausea',
                'skin rash,redness,itching,bumps',
                'itching,red patches',
                'skin irritation,redness',
                'joint pain,fatigue,stiffness',
                'hand pain,swelling',
                'back pain,stiffness',
                'fatigue,headache,weakness',
                'tiredness,weakness',
                'pale skin,dizziness',
                'cough,chest tightness,shortness of breath',
                'wheezing,coughing fits',
                'breathing difficulty,chest tightness',
                'red eyes,itching,sticky discharge',
                'eye redness,pain,discharge',
                'watery eyes,redness',
                'ear pain,fullness,fever',
                'earache,discharge,fever',
                'ear pain,ringing',
                'sore throat,painful swallowing,fever',
                'throat pain,hoarse voice',
                'swollen throat,fever',
                'fever,chills,headache,body ache',
                'high fever,cough,body ache',
                'fever,sore throat,headache',
                'cough,sneezing,watery eyes',
                'runny nose,cough,headache',
                'congestion,sneezing,cough',
                'severe stomach pain,vomiting',
                'nausea,stomach cramps,diarrhea',
                'vomiting,dehydration',
                'chest pain,arm numbness',
                'chest pressure,shortness of breath',
                'irregular heartbeat,chest pain',
                'severe headache,light sensitivity,sound sensitivity',
                'migraine headache,nausea,vomiting',
                'pulsating headache',
                'widespread rash,itching',
                'allergic reaction,itching,hives',
                'contact dermatitis,redness',
                'multiple joint pain,swelling',
                'joint pain,warmth,redness',
                'chronic joint pain',
                'severe fatigue,shortness of breath',
                'anemia symptoms,fatigue',
                'weakness,fatigue,pale',
                'chronic cough,wheezing',
                'asthma attack,shortness of breath',
                'exercise induced wheezing',
                'pink eye,redness,discharge',
                'bacterial conjunctivitis,discharge',
                'viral conjunctivitis,redness',
                'middle ear infection,pain',
                'otitis media,fever',
                'ear infection,discharge',
                'strep throat,fever',
                'tonsillitis,sore throat',
                'pharyngitis,throat pain'
            ],
            'disease': [
                'Common Cold', 'Flu', 'Common Cold', 'Common Cold', 'Flu', 'Flu', 'Flu',
                'Migraine', 'Migraine', 'Migraine', 'Migraine',
                'Cardiac Issue', 'Cardiac Issue', 'Cardiac Issue', 'Cardiac Issue',
                'Skin Allergy', 'Skin Allergy', 'Skin Allergy', 'Skin Allergy',
                'Gastroenteritis', 'Gastroenteritis', 'Gastroenteritis', 'Gastroenteritis',
                'Arthritis', 'Arthritis', 'Arthritis', 'Arthritis',
                'Anemia', 'Anemia', 'Anemia', 'Anemia',
                'Asthma', 'Asthma', 'Asthma', 'Asthma',
                'Conjunctivitis', 'Conjunctivitis', 'Conjunctivitis', 'Conjunctivitis',
                'Ear Infection', 'Ear Infection', 'Ear Infection', 'Ear Infection',
                'Throat Infection', 'Throat Infection', 'Throat Infection', 'Throat Infection',
                'Flu', 'Flu', 'Common Cold', 'Common Cold', 'Common Cold',
                'Gastroenteritis', 'Gastroenteritis', 'Gastroenteritis',
                'Cardiac Issue', 'Cardiac Issue', 'Cardiac Issue',
                'Migraine', 'Migraine', 'Migraine',
                'Skin Allergy', 'Skin Allergy', 'Skin Allergy',
                'Arthritis', 'Arthritis', 'Arthritis',
                'Anemia', 'Anemia', 'Anemia',
                'Asthma', 'Asthma', 'Asthma',
                'Conjunctivitis', 'Conjunctivitis', 'Conjunctivitis',
                'Ear Infection', 'Ear Infection', 'Ear Infection',
                'Throat Infection', 'Throat Infection', 'Throat Infection',
                'Flu', 'Flu', 'Flu',
                'Common Cold', 'Common Cold', 'Common Cold',
                'Gastroenteritis', 'Gastroenteritis', 'Gastroenteritis',
                'Cardiac Issue', 'Cardiac Issue', 'Cardiac Issue',
                'Migraine', 'Migraine', 'Migraine',
                'Skin Allergy', 'Skin Allergy', 'Skin Allergy',
                'Arthritis', 'Arthritis', 'Arthritis',
                'Anemia', 'Anemia', 'Anemia',
                'Asthma', 'Asthma', 'Asthma',
                'Conjunctivitis', 'Conjunctivitis', 'Conjunctivitis',
                'Ear Infection', 'Ear Infection', 'Ear Infection',
                'Throat Infection', 'Throat Infection', 'Throat Infection'
            ]
        }
        
        df = pd.DataFrame(sample_data)
        df.to_csv(data_path, index=False)
        print(f"Sample training data created at {data_path}")

# Global instance
predictor = DiseasePredictor()

