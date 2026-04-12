"""
Simple script to run the application
"""
from app import app
import os

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    print("=" * 50)
    print("Smart Healthcare Assistant")
    print("=" * 50)
    print("Starting server...")
    print("Open your browser and navigate to: http://localhost:5000")
    print("Admin Login: http://localhost:5000/admin/login")
    print("Default Admin Credentials:")
    print("  Username: admin")
    print("  Password: admin123")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)


