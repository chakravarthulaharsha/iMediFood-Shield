import json
import hmac
import csv
import shutil
import hashlib
import statistics
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SECURITY_DIR = BASE_DIR / "security"
RESULTS_DIR = BASE_DIR / "paper_ready_results" / "raspberry_pi"
DEMO_DIR = SECURITY_DIR / "rpi_validation_timing_demo"

SIGNED_MANIFEST_PATH = SECURITY_DIR / "rpi_security_manifest_v1_signed.json"
KEY_PATH = SECURITY_DIR / "demo_hmac_key_DO_NOT_SHARE.key"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
DEMO_DIR.mkdir(exist_ok=True)

N_RUNS = 30

def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sha256_file(path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk_size)
            if not b:
                break
            h.update(b)
    return h.hexdigest()

with open(SIGNED_MANIFEST_PATH, "r", encoding="utf-8") as f:
    signed_manifest = json.load(f)

key = KEY_PATH.read_bytes()
manifest = signed_manifest["manifest"]
expected_manifest_sig = signed_manifest["manifest_hmac_sha256"]

def verify_manifest():
    current_manifest_sig = hmac.new(
        key,
        canonical_json(manifest),
        hashlib.sha256
    ).hexdigest()

    manifest_signature_match = current_manifest_sig == expected_manifest_sig

    all_files_ok = True
    for asset in manifest["protected_assets"]:
        asset_path = BASE_DIR / asset["relative_path"]
        current_hash = sha256_file(asset_path)
        if current_hash != asset["sha256"]:
            all_files_ok = False

    if manifest_signature_match and all_files_ok:
        return "VERIFIED_PROVENANCE"
    return "FAILED_VERIFICATION"

# Create a tampered copy for failed-validation timing.
target_asset = manifest["protected_assets"][0]
original_path = BASE_DIR / target_asset["relative_path"]
tampered_path = DEMO_DIR / ("tampered_" + original_path.name)

shutil.copy2(original_path, tampered_path)
with open(tampered_path, "ab") as f:
    f.write(b"\nRPI_VALIDATION_TIMING_TAMPER")

def verify_tampered_copy():
    current_hash = sha256_file(tampered_path)
    if current_hash == target_asset["sha256"]:
        return "VERIFIED_PROVENANCE"
    return "FAILED_VERIFICATION"

verified_times = []
failed_times = []

for _ in range(N_RUNS):
    start = time.perf_counter()
    status = verify_manifest()
    end = time.perf_counter()
    verified_times.append((end - start) * 1000)

for _ in range(N_RUNS):
    start = time.perf_counter()
    failed_status = verify_tampered_copy()
    end = time.perf_counter()
    failed_times.append((end - start) * 1000)

summary = {
    "runs": N_RUNS,
    "verified_status": status,
    "failed_status": failed_status,
    "protected_assets": len(manifest["protected_assets"]),
    "verified_mean_ms": round(statistics.mean(verified_times), 3),
    "verified_std_ms": round(statistics.stdev(verified_times), 3),
    "verified_min_ms": round(min(verified_times), 3),
    "verified_max_ms": round(max(verified_times), 3),
    "failed_mean_ms": round(statistics.mean(failed_times), 3),
    "failed_std_ms": round(statistics.stdev(failed_times), 3),
    "failed_min_ms": round(min(failed_times), 3),
    "failed_max_ms": round(max(failed_times), 3),
}

csv_path = RESULTS_DIR / "rpi_validation_timing.csv"
txt_path = RESULTS_DIR / "rpi_validation_timing_summary.txt"

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
    writer.writeheader()
    writer.writerow(summary)

with open(txt_path, "w", encoding="utf-8") as f:
    f.write("Raspberry Pi Security Validation Timing\n")
    f.write("=" * 60 + "\n")
    for k, v in summary.items():
        f.write(f"{k}: {v}\n")

print("Raspberry Pi Security Validation Timing")
print("=" * 60)
for k, v in summary.items():
    print(f"{k}: {v}")

print("\nSaved:")
print(csv_path)
print(txt_path)
