import os
import json
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

from src.utils.text_utils import normalize_name
from src.security.security_utils import sha256_text, hmac_sign_record

class MediFoodShieldEngine:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)

        self.processed_dir = self.base_dir / "data_processed"
        self.model_dir = self.base_dir / "models"
        self.security_dir = self.base_dir / "security"

        self.lookup_path = self.processed_dir / "ddid_evidence_lookup_guard_table.csv"
        self.model_path = self.model_dir / "medsafe_gate_v1_calibrated_linearsvc.joblib"
        self.key_path = self.security_dir / "demo_hmac_key_DO_NOT_SHARE.key"
        self.signed_manifest_path = self.security_dir / "security_manifest_v1_signed.json"

        self.lookup_df = pd.read_csv(self.lookup_path)
        self.model = joblib.load(self.model_path)

        with open(self.key_path, "rb") as f:
            self.demo_key = f.read()

        with open(self.signed_manifest_path, "r", encoding="utf-8") as f:
            self.signed_manifest = json.load(f)

        self.manifest = self.signed_manifest["manifest"]

        self.protected_hashes = {
            item["logical_name"]: item["sha256"]
            for item in self.manifest["protected_files"]
        }

        self.label_priority = {
            "Avoid": 3,
            "Use caution": 2,
            "No known interaction in selected source": 1,
            "Insufficient evidence": 0
        }

        self._build_fast_lookup()

    def _build_fast_lookup(self):
        df = self.lookup_df.copy()
        df["lookup_priority"] = df["paper_label"].map(self.label_priority).fillna(0)

        lookup_sorted = df.sort_values(
            by=["drug_name_norm", "food_herb_name_norm", "lookup_priority", "evidence_row_count"],
            ascending=[True, True, False, False]
        )

        lookup_dedup = lookup_sorted.drop_duplicates(
            subset=["drug_name_norm", "food_herb_name_norm"],
            keep="first"
        ).copy()

        self.fast_lookup = {}

        for _, row in lookup_dedup.iterrows():
            key = (
                str(row["drug_name_norm"]).strip(),
                str(row["food_herb_name_norm"]).strip()
            )
            self.fast_lookup[key] = row.to_dict()

        self.known_drugs = set(
            self.lookup_df["drug_name_norm"].dropna().astype(str).str.strip()
        )

        self.known_items = set(
            self.lookup_df["food_herb_name_norm"].dropna().astype(str).str.strip()
        )

        self.drug_choices = (
            self.lookup_df[["Drug_Name", "drug_name_norm"]]
            .dropna()
            .drop_duplicates()
            .sort_values("Drug_Name")["Drug_Name"]
            .tolist()
        )

        self.food_choices = (
            self.lookup_df[["Food_Herb_Name", "food_herb_name_norm"]]
            .dropna()
            .drop_duplicates()
            .sort_values("Food_Herb_Name")["Food_Herb_Name"]
            .tolist()
        )

        self.item_type_map = (
            self.lookup_df.groupby("food_herb_name_norm")["Type"]
            .agg(lambda x: x.value_counts().index[0])
            .to_dict()
        )

        self.drug_norm_to_display = {}
        for d in self.drug_choices:
            self.drug_norm_to_display[normalize_name(d)] = d

        self.drug_norm_choices = list(self.drug_norm_to_display.keys())

    def ddid_evidence_lookup_fast(self, drug_name, food_herb_name):
        drug_norm = normalize_name(drug_name)
        item_norm = normalize_name(food_herb_name)

        key = (drug_norm, item_norm)

        if key not in self.fast_lookup:
            return None

        best = self.fast_lookup[key]

        return {
            "source": "DDID Evidence Lookup Guard",
            "found_in_ddid": True,
            "drug_known_in_ddid": True,
            "item_known_in_ddid": True,
            "drug_name_input": drug_name,
            "food_herb_name_input": food_herb_name,
            "drug_name_norm": drug_norm,
            "food_herb_name_norm": item_norm,
            "pair_key": best.get("pair_key", ""),
            "Drug_ID": best.get("Drug_ID", ""),
            "Food_Herb_ID": best.get("Food_Herb_ID", ""),
            "Drug_Name": best.get("Drug_Name", ""),
            "Food_Herb_Name": best.get("Food_Herb_Name", ""),
            "Type": best.get("Type", ""),
            "recommendation_label": best.get("paper_label", ""),
            "effect_clean": best.get("effect_clean", ""),
            "ddid_effects_all": best.get("ddid_effects_all", ""),
            "Conclusion": best.get("Conclusion", ""),
            "Reference": best.get("Reference", ""),
            "DOI": best.get("DOI", ""),
            "Relationship_classification": best.get("Relationship_classification", ""),
            "evidence_row_count": int(best.get("evidence_row_count", 0)),
            "final_decision_source": "DDID exact-pair evidence lookup",
            "coverage_guard_applied": False
        }

    def model_predict_with_safety_gate(self, drug_name, food_herb_name, item_type="unknown", threshold=0.7):
        drug_norm = normalize_name(drug_name)
        item_norm = normalize_name(food_herb_name)
        type_norm = normalize_name(item_type)

        drug_item_text = f"{drug_norm} [SEP] {item_norm} [SEP] {type_norm}"

        probs = self.model.predict_proba([drug_item_text])[0]
        classes = list(self.model.classes_)

        pred_idx = int(np.argmax(probs))
        raw_prediction = classes[pred_idx]

        final_prediction = raw_prediction
        gate_applied = False

        no_known_label = "No known interaction in selected source"

        if no_known_label in classes:
            no_known_idx = classes.index(no_known_label)
            no_known_prob = probs[no_known_idx]

            if raw_prediction == no_known_label and no_known_prob < threshold:
                final_prediction = "Use caution"
                gate_applied = True

        prob_dict = {
            f"prob_{normalize_name(cls).replace(' ', '_')}": float(probs[i])
            for i, cls in enumerate(classes)
        }

        return {
            "source": "MedSafe-GATE v1 model branch",
            "found_in_ddid": False,
            "drug_known_in_ddid": True,
            "item_known_in_ddid": True,
            "drug_name_input": drug_name,
            "food_herb_name_input": food_herb_name,
            "drug_name_norm": drug_norm,
            "food_herb_name_norm": item_norm,
            "item_type_input": item_type,
            "drug_item_text": drug_item_text,
            "raw_model_prediction": raw_prediction,
            "recommendation_label": final_prediction,
            "safety_gate_threshold": threshold,
            "safety_gate_applied": gate_applied,
            "final_decision_source": "Known-entity model branch with safety gate",
            "coverage_guard_applied": False,
            **prob_dict
        }

    def recommend(self, drug_name, food_herb_name, threshold=0.7):
        drug_norm = normalize_name(drug_name)
        item_norm = normalize_name(food_herb_name)

        lookup_result = self.ddid_evidence_lookup_fast(drug_name, food_herb_name)

        if lookup_result is not None:
            return lookup_result

        drug_known = drug_norm in self.known_drugs
        item_known = item_norm in self.known_items

        if not drug_known or not item_known:
            return {
                "source": "Input Coverage Guard",
                "found_in_ddid": False,
                "drug_known_in_ddid": drug_known,
                "item_known_in_ddid": item_known,
                "drug_name_input": drug_name,
                "food_herb_name_input": food_herb_name,
                "drug_name_norm": drug_norm,
                "food_herb_name_norm": item_norm,
                "recommendation_label": "Insufficient evidence",
                "final_decision_source": "Coverage guard blocked out-of-vocabulary model prediction",
                "coverage_guard_applied": True,
                "reason": (
                    "The drug and/or food/herb item was not found in the DDID vocabulary. "
                    "The system does not make a model-based recommendation for out-of-coverage inputs."
                )
            }

        item_type = self.item_type_map.get(item_norm, "unknown")

        return self.model_predict_with_safety_gate(
            drug_name=drug_name,
            food_herb_name=food_herb_name,
            item_type=item_type,
            threshold=threshold
        )

    def sign_recommendation_output(self, result):
        record_body = {
            "record_type": "MediFoodShield signed recommendation",
            "record_version": "v1.0",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "input": {
                "drug_name_input": str(result.get("drug_name_input", "")),
                "food_herb_name_input": str(result.get("food_herb_name_input", "")),
                "drug_name_norm": str(result.get("drug_name_norm", "")),
                "food_herb_name_norm": str(result.get("food_herb_name_norm", ""))
            },
            "decision": {
                "recommendation_label": str(result.get("recommendation_label", "")),
                "source": str(result.get("source", "")),
                "final_decision_source": str(result.get("final_decision_source", "")),
                "found_in_ddid": str(result.get("found_in_ddid", "")),
                "coverage_guard_applied": str(result.get("coverage_guard_applied", ""))
            },
            "asset_hashes": {
                "ddid_lookup_table_sha256": self.protected_hashes.get("ddid_lookup_table", ""),
                "model_file_sha256": self.protected_hashes.get("model_file", ""),
                "inference_policy_sha256": self.protected_hashes.get("inference_policy", "")
            },
            "output_hash": sha256_text(
                str(result.get("drug_name_input", ""))
                + "|"
                + str(result.get("food_herb_name_input", ""))
                + "|"
                + str(result.get("recommendation_label", ""))
                + "|"
                + str(result.get("source", ""))
                + "|"
                + str(result.get("final_decision_source", ""))
            )
        }

        signature = hmac_sign_record(record_body, self.demo_key)

        return {
            "record_body": record_body,
            "record_signature_hmac_sha256": signature
        }

    def recommend_and_sign(self, drug_name, food_herb_name, threshold=0.7):
        result = self.recommend(drug_name, food_herb_name, threshold)
        signed_record = self.sign_recommendation_output(result)
        return result, signed_record
