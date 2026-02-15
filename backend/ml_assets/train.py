import pandas as pd
import numpy as np
import joblib
import re
import os
import json
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import VotingClassifier

# ---------------------------
# Output folder
# ---------------------------
OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------
# Load dataset
# ---------------------------
df = pd.read_csv("Symptom2Disease.csv")

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[^a-z\s]', '', text)
    return text

df["text"] = df["text"].apply(clean_text)

X = df["text"]
y = df["label"]

# ---------------------------
# Encode labels
# ---------------------------
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# ---------------------------
# TF-IDF
# ---------------------------
vectorizer = TfidfVectorizer(
    max_features=30000,
    ngram_range=(1,4),
    stop_words="english",
    sublinear_tf=True,
    min_df=2,
    max_df=0.9
)

X_tfidf = vectorizer.fit_transform(X)

# ---------------------------
# Split
# ---------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X_tfidf,
    y_encoded,
    test_size=0.2,
    random_state=42,
    stratify=y_encoded
)

# ---------------------------
# Models
# ---------------------------
log_reg = LogisticRegression(
    max_iter=7000,
    C=5,
    solver='lbfgs',
    class_weight='balanced'
)

svc = SVC(
    C=2,
    kernel='linear',
    probability=True,
    class_weight='balanced'
)

model = VotingClassifier(
    estimators=[('lr', log_reg), ('svc', svc)],
    voting='soft'
)

# ---------------------------
# Train
# ---------------------------
model.fit(X_train, y_train)

# ---------------------------
# Evaluation
# ---------------------------
y_pred = model.predict(X_test)
top1_accuracy = accuracy_score(y_test, y_pred)

probabilities = model.predict_proba(X_test)
top3_predictions = np.argsort(probabilities, axis=1)[:, -3:]

top3_correct = sum(1 for i in range(len(y_test)) if y_test[i] in top3_predictions[i])
top3_accuracy = top3_correct / len(y_test)

print("\n==============================")
print("TOP-1 ACCURACY:", round(top1_accuracy * 100, 2), "%")
print("TOP-3 ACCURACY:", round(top3_accuracy * 100, 2), "%")
print("==============================\n")

report_txt = classification_report(y_test, y_pred)
print(report_txt)

# Cross validation
cv_scores = cross_val_score(model, X_tfidf, y_encoded, cv=5)
cv_mean = float(np.mean(cv_scores))
print("Mean CV Accuracy:", round(cv_mean * 100, 2), "%")

# ---------------------------
# Save model files
# ---------------------------
joblib.dump(model, "disease_model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")
joblib.dump(label_encoder, "label_encoder.pkl")
print("\nModel Saved Successfully!")

# ---------------------------
# Save metrics as JSON (for reports page)
# ---------------------------
report_dict = classification_report(y_test, y_pred, output_dict=True)

metrics = {
    "top1_accuracy": round(float(top1_accuracy), 6),
    "top3_accuracy": round(float(top3_accuracy), 6),
    "cv_mean_accuracy": round(cv_mean, 6),
    "classification_report": report_dict
}

with open(os.path.join(OUT_DIR, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)

# ---------------------------
# Confusion matrix plot
# ---------------------------
cm = confusion_matrix(y_test, y_pred)

plt.figure()
plt.imshow(cm)
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.colorbar()
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "confusion_matrix.png"))
plt.close()

# ---------------------------
# CV plot
# ---------------------------
plt.figure()
plt.plot(range(1, len(cv_scores) + 1), cv_scores, marker="o")
plt.title("Cross Validation Scores")
plt.xlabel("Fold")
plt.ylabel("Accuracy")
plt.ylim(0, 1)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "cross_validation.png"))
plt.close()

# ---------------------------
# Class distribution plot
# ---------------------------
counts = df["label"].value_counts().sort_values(ascending=False)
plt.figure()
plt.bar(counts.index, counts.values)
plt.title("Class Distribution")
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "class_distribution.png"))
plt.close()

# ---------------------------
# Accuracy as simple plot
# ---------------------------
plt.figure()
plt.bar(["Top1", "Top3", "CV Mean"], [top1_accuracy, top3_accuracy, cv_mean])
plt.title("Accuracy Summary")
plt.ylim(0, 1)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "accuracy.png"))
plt.close()

print(f"\n✅ Saved outputs to: {OUT_DIR}/")
print("✅ metrics.json + plots generated.")
