from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional
import os, joblib
import numpy as np

from app.auth import get_current_user

router = APIRouter(prefix="/symptom", tags=["ML Prediction"])

# ---- Load pkl files from backend root ----
#BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MODEL_PATH = os.path.join(BACKEND_DIR, "disease_model.pkl")
VECTORIZER_PATH = os.path.join(BACKEND_DIR, "vectorizer.pkl")
ENCODER_PATH = os.path.join(BACKEND_DIR, "label_encoder.pkl")

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)
label_encoder = joblib.load(ENCODER_PATH)

class MLIn(BaseModel):
    symptoms: List[str]
    top_k: Optional[int] = 5

@router.post("/predict-ml")
def predict_ml(body: MLIn, user=Depends(get_current_user)):
    # selected symptoms -> single text
    text = ", ".join([s.strip().lower() for s in body.symptoms if s and s.strip()])
    X = vectorizer.transform([text])

    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)[0]
        k = max(1, min(int(body.top_k or 5), 10))
        top_idx = np.argsort(probs)[::-1][:k]

        diseases = label_encoder.inverse_transform(top_idx)
        preds = [
            {"disease": str(d), "confidence": round(float(probs[i]), 4)}
            for d, i in zip(diseases, top_idx)
        ]
        return {"predictions": preds}

    # fallback
    pred = model.predict(X)[0]
    disease = label_encoder.inverse_transform([pred])[0]
    return {"predictions": [{"disease": str(disease), "confidence": None}]}
