import os
import json
import hmac
import csv
import shutil
import hashlib
import platform
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parents[1]
SECURITY_DIR = BASE_DIR / "security"
RPI_RESULTS_DIR = BASE_DIR / "paper_ready_results" / "raspberry_pi"
TAMPER_DIR = SECURITY_DIR / "rpi_tamper_tests"

SECURITY_DIR.mkdir(exist_ok=True)
RPI_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
TAMPER_DIR.mkdir(exist_ok=True)

KEY_PATH = SECURITY_DIR / "demo_hmac_key_DO_NOT_SHARE.key"

if not KEY_PATH.exists():
    KEY_PATH.write_bytes(os.urandom(32))

KEY = KEY_PATH.read_bytes()

# Create/update Raspberry Pi policy file so policy tampering can be tested.
policy_path = SECURITY_DIR / "rpi_inference_policy.json"
policy = {
    "policy_name": "MediFoodShield Raspberry Pi inference policy",
    "framework": "MediFoodShield",
    "coverage_guard": "enabled",
    "evidence_lookup_guard": "enabled",
    "recommendation_signing": "enabled",
    "security_mode": "software_hmac_sha256_tamper_evident",
    "note": "Software HMAC prototype; not hardware-rooted secure element."
}
policy_path.write_text(json.dumps(policy, indent=2), encoding="utf-8")

protected_files = {
    "ddid_lookup_table": "data_processed/ddid_evidence_lookup_guard_table.csv",
    "model_file": "models/medsafe_gate_v1_calibrated_linearsvc.joblib",
    "inference_policy": "security/rpi_inference_policy.json",
    "rpi_backend_output_log": "paper_ready_results/raspberry_pi/rpi_backend_test.txt",
    "signed_recommendation_records": "security/step19_signed_recommendation_records.json",
}

def sha256_file(path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

assets = []
missing = []

for name, rel_path in protected_files.items():
    abs_path = BASE_DIR / rel_path
    if abs_path.exists():
        assets.append({
            "asset_name": name,
            "relative_path": rel_path,
            "size_bytes": abs_path.stat().st_size,
            "sha256": sha256_file(abs_path)
        })
    else:
        missing.append({"asset_name": name, "relative_path": rel_path})

manifest = {
    "manifest_name": "MediFoodShield Raspberry Pi Security Manifest",
    "manifest_version": "rpi_v1.0",
    "created_utc": datetime.utcnow().isoformat() + "Z",
    "hash_algorithm": "SHA-256",
    "signature_algorithm": "HMAC-SHA256",
    "device_platform": {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version()
    },
    "protected_assets": assets,
    "missing_assets": missing
}

sig = hmac.new(KEY, canonical_json(manifest), hashlib.sha256).hexdigest()

signed_manifest = {
    "manifest": manifest,
    "manifest_hmac_sha256": sig
}

unsigned_path = SECURITY_DIR / "rpi_security_manifest_v1_unsigned.json"
signed_path = SECURITY_DIR / "rpi_security_manifest_v1_signed.json"
verify_path = SECURITY_DIR / "rpi_security_manifest_v1_verification_result.json"

unsigned_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
signed_path.write_text(json.dumps(signed_manifest, indent=2), encoding="utf-8")

# Verify manifest and protected files.
expected_sig = signed_manifest["manifest_hmac_sha256"]
current_sig = hmac.new(KEY, canonical_json(signed_manifest["manifest"]), hashlib.sha256).hexdigest()

file_results = []
all_files_ok = True

for asset in assets:
    p = BASE_DIR / asset["relative_path"]
    current_hash = sha256_file(p)
    ok = current_hash == asset["sha256"]
    all_files_ok = all_files_ok and ok
    file_results.append({
        "asset_name": asset["asset_name"],
        "relative_path": asset["relative_path"],
        "expected_sha256": asset["sha256"],
        "current_sha256": current_hash,
        "status": "MATCH" if ok else "MISMATCH"
    })

verification_status = "VERIFIED_PROVENANCE" if expected_sig == current_sig and all_files_ok else "FAILED_VERIFICATION"

verification = {
    "verification_status": verification_status,
    "manifest_signature_match": expected_sig == current_sig,
    "all_file_hashes_match": all_files_ok,
    "file_results": file_results,
    "missing_assets": missing
}

verify_path.write_text(json.dumps(verification, indent=2), encoding="utf-8")

# Safe tamper tests using copied files only.
attack_plan = [
    ("DDID lookup table tampering", "ddid_lookup_table"),
    ("Model file tampering", "model_file"),
    ("Policy modification / rollback", "inference_policy"),
    ("Backend output log tampering", "rpi_backend_output_log"),
    ("Signed recommendation output tampering", "signed_recommendation_records"),
]

asset_map = {a["asset_name"]: a for a in assets}
attack_rows = []

for attack_name, asset_name in attack_plan:
    if asset_name not in asset_map:
        attack_rows.append({
            "attack": attack_name,
            "asset": asset_name,
            "expected_result": "FAILED_VERIFICATION",
            "observed_result": "SKIPPED_ASSET_MISSING",
            "detected": "No"
        })
        continue

    asset = asset_map[asset_name]
    original = BASE_DIR / asset["relative_path"]
    tampered = TAMPER_DIR / ("tampered_" + original.name)

    shutil.copy2(original, tampered)

    with open(tampered, "ab") as f:
        f.write(b"\nRPI_TAMPER_TEST_CHANGE")

    tampered_hash = sha256_file(tampered)
    detected = tampered_hash != asset["sha256"]

    attack_rows.append({
        "attack": attack_name,
        "asset": asset_name,
        "expected_result": "FAILED_VERIFICATION",
        "observed_result": "FAILED_VERIFICATION" if detected else "VERIFIED_PROVENANCE",
        "detected": "Yes" if detected else "No"
    })

attack_csv = SECURITY_DIR / "rpi_security_attack_detection.csv"
with open(attack_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["attack", "asset", "expected_result", "observed_result", "detected"])
    writer.writeheader()
    writer.writerows(attack_rows)

detected_count = sum(1 for r in attack_rows if r["detected"] == "Yes")
total_count = len(attack_rows)

attack_summary = {
    "detected_attacks": detected_count,
    "total_attacks": total_count,
    "attack_detection_rate_percent": round(100 * detected_count / total_count, 2),
    "attack_results_csv": str(attack_csv)
}

summary_path = SECURITY_DIR / "rpi_security_attack_summary.json"
summary_path.write_text(json.dumps(attack_summary, indent=2), encoding="utf-8")

# Copy important outputs to paper-ready Raspberry Pi folder.
for p in [unsigned_path, signed_path, verify_path, attack_csv, summary_path]:
    shutil.copy2(p, RPI_RESULTS_DIR / p.name)

print("=" * 70)
print("Raspberry Pi security refresh complete")
print("=" * 70)
print("Signed manifest:", signed_path)
print("Verification result:", verification_status)
print("Protected assets:", len(assets))
print("Missing assets:", len(missing))
print("Attack detection:", f"{detected_count}/{total_count}")
print("Attack detection rate:", f"{attack_summary['attack_detection_rate_percent']}%")
print("Paper-ready folder:", RPI_RESULTS_DIR)
