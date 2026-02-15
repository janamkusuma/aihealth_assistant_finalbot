# backend/app/services/ml_predictor.py
import os
import joblib
import numpy as np

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))  # -> backend/

MODEL_PATH = os.path.join(BACKEND_DIR, "disease_model.pkl")
VECTORIZER_PATH = os.path.join(BACKEND_DIR, "vectorizer.pkl")
ENCODER_PATH = os.path.join(BACKEND_DIR, "label_encoder.pkl")

_model = joblib.load(MODEL_PATH)
_vectorizer = joblib.load(VECTORIZER_PATH)
_encoder = joblib.load(ENCODER_PATH)

def predict_top(symptoms_text: str, top_k: int = 5):
    X = _vectorizer.transform([symptoms_text])

    # If model supports predict_proba -> best
    if hasattr(_model, "predict_proba"):
        probs = _model.predict_proba(X)[0]  # array
        top_idx = np.argsort(probs)[::-1][:top_k]

        diseases = _encoder.inverse_transform(top_idx)
        results = [{"disease": d, "confidence": float(probs[i])} for d, i in zip(diseases, top_idx)]
        return results

    # Fallback: only 1 prediction available
    pred = _model.predict(X)[0]
    disease = _encoder.inverse_transform([pred])[0]
    return [{"disease": disease, "confidence": None}]
