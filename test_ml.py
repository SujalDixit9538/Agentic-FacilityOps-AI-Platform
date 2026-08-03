import joblib
import pandas as pd
from pathlib import Path
import traceback
import sklearn

print(f"Scikit-Learn Version: {sklearn.__version__}")

try:
    # 1. Test Path and Loading
    base_dir = Path.cwd()
    model_path = base_dir / "models" / "energy_model_total_v1.joblib"
    print(f"Attempting to load model from: {model_path}")
    
    if not model_path.exists():
        print("❌ ERROR: File does not exist at this path!")
        exit(1)
        
    model = joblib.load(model_path)
    print("✅ Model loaded successfully!")
    
    # 2. Test Inference (Matching the 5 features from Kaggle)
    dummy_data = pd.DataFrame([{
        'hour': 14, 
        'day_of_week': 2, 
        'month': 7, 
        'is_weekend': 0, 
        'air_temperature': 25.5
    }])
    
    print("Attempting prediction...")
    prediction = model.predict(dummy_data)
    print(f"✅ Prediction successful! Predicted Total kWh: {prediction[0]:.2f}")

except Exception as e:
    print("\n❌ ML PIPELINE FAILED. Here is the exact error:")
    traceback.print_exc()