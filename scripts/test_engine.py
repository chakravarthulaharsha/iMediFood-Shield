from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.core.medifood_engine import MediFoodShieldEngine

engine = MediFoodShieldEngine(BASE_DIR)

tests = [
    ("Ibuprofen", "Ginkgo Biloba"),
    ("Omeprazole", "Grapefruit"),
    ("Atorvastatin", "High-Fat Meal"),
    ("RandomDrugXYZ", "RandomFoodXYZ")
]

for drug, item in tests:
    result, signed_record = engine.recommend_and_sign(drug, item, threshold=0.7)
    print("=" * 60)
    print("Drug:", drug)
    print("Food/Herb:", item)
    print("Recommendation:", result.get("recommendation_label"))
    print("Decision source:", result.get("final_decision_source"))
    print("Signed:", "record_signature_hmac_sha256" in signed_record)
