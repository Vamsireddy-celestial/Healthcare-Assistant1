"""
Script to train the disease prediction model
"""
from ml_model import DiseasePredictor

if __name__ == '__main__':
    print("Training disease prediction model...")
    predictor = DiseasePredictor()
    predictor.train()
    print("Training completed!")

