import pandas as pd
from backend.agents.maintenance.analyzer import MaintenanceAnalyzer

analyzer = MaintenanceAnalyzer()
# Mock load_models check
analyzer._load_models()

def test_features(wear, torque, speed, air_temp=300.0, process_temp=310.0):
    features_df = pd.DataFrame([{
        'Type': 1,
        'Air temperature [K]': air_temp,
        'Process temperature [K]': process_temp,
        'Rotational speed [rpm]': speed,
        'Torque [Nm]': torque,
        'Tool wear [min]': wear
    }])
    
    failure_probs = analyzer.failure_model.predict_proba(features_df)[0]
    prob_failure = float(failure_probs[1])
    health_score = max(0.0, min(100.0, (1.0 - prob_failure) * 100))
    return prob_failure, health_score

# Case 1: Extreme Failure Territory
p1, h1 = test_features(230, 62, 1250)
print(f"Extreme Failure Case (Wear=230, Torque=62, Speed=1250):")
print(f"  Failure Probability: {p1:.4f}")
print(f"  Health Score: {h1:.2f}")

# Case 2: Opposite extreme
p2, h2 = test_features(5, 25, 1500)
print(f"Optimal Case (Wear=5, Torque=25, Speed=1500):")
print(f"  Failure Probability: {p2:.4f}")
print(f"  Health Score: {h2:.2f}")
