import os
import joblib
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

BASE_DIR = "/home/pi/Desktop/MediFoodShield"
processed_dir = os.path.join(BASE_DIR, "data_processed")
model_dir = os.path.join(BASE_DIR, "models")

train_path = os.path.join(processed_dir, "train_ddid_only.csv")
model_path = os.path.join(model_dir, "medsafe_gate_v1_calibrated_linearsvc.joblib")
backup_path = os.path.join(model_dir, "medsafe_gate_v1_calibrated_linearsvc_colab_backup.joblib")

print("Loading:", train_path)
train_df = pd.read_csv(train_path)

X_train = train_df["drug_item_text"].fillna("")
y_train = train_df["paper_label"]

print("Train rows:", len(train_df))
print("Labels:")
print(y_train.value_counts())

base_svc = LinearSVC(
    class_weight="balanced",
    random_state=42,
    max_iter=5000
)

try:
    calibrated_svc = CalibratedClassifierCV(
        estimator=base_svc,
        method="sigmoid",
        cv=3
    )
except TypeError:
    calibrated_svc = CalibratedClassifierCV(
        base_estimator=base_svc,
        method="sigmoid",
        cv=3
    )

model = Pipeline([
    ("tfidf", TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=2
    )),
    ("clf", calibrated_svc)
])

print("Training Raspberry Pi-compatible MedSafe-GATE model...")
model.fit(X_train, y_train)

if os.path.exists(model_path) and not os.path.exists(backup_path):
    os.rename(model_path, backup_path)
    print("Backed up Colab model to:", backup_path)

joblib.dump(model, model_path)

print("Saved Raspberry Pi-compatible model to:", model_path)
print("Done.")
