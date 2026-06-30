import json
import hmac
import hashlib
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SECURITY_DIR = BASE_DIR / "security"

SIGNED_MANIFEST_PATH = SECURITY_DIR / "rpi_security_manifest_v1_signed.json"
KEY_PATH = SECURITY_DIR / "demo_hmac_key_DO_NOT_SHARE.key"
DEMO_DIR = SECURITY_DIR / "rpi_command_prompt_demo"
DEMO_DIR.mkdir(exist_ok=True)

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

key = KEY_PATH.read_bytes()

with open(SIGNED_MANIFEST_PATH, "r", encoding="utf-8") as f:
    signed_manifest = json.load(f)

manifest = signed_manifest["manifest"]
expected_manifest_sig = signed_manifest["manifest_hmac_sha256"]
current_manifest_sig = hmac.new(key, canonical_json(manifest), hashlib.sha256).hexdigest()

manifest_signature_match = expected_manifest_sig == current_manifest_sig

all_files_ok = True
for asset in manifest["protected_assets"]:
    asset_path = BASE_DIR / asset["relative_path"]
    current_hash = sha256_file(asset_path)
    if current_hash != asset["sha256"]:
        all_files_ok = False

verified_status = "VERIFIED_PROVENANCE" if manifest_signature_match and all_files_ok else "FAILED_VERIFICATION"

print("=" * 70)
print("CASE 1: ORIGINAL RASPBERRY PI DEPLOYMENT")
print("=" * 70)
print("Manifest signature match:", manifest_signature_match)
print("All protected file hashes match:", all_files_ok)
print("Verification result:", verified_status)

# Safe failed demo: copy one protected file, tamper the copy, compare with original expected hash.
target_asset = manifest["protected_assets"][0]
original_path = BASE_DIR / target_asset["relative_path"]
tampered_path = DEMO_DIR / ("tampered_" + original_path.name)

shutil.copy2(original_path, tampered_path)

with open(tampered_path, "ab") as f:
    f.write(b"\nCOMMAND_PROMPT_TAMPER_TEST")

expected_hash = target_asset["sha256"]
tampered_hash = sha256_file(tampered_path)

tamper_detected = expected_hash != tampered_hash
failed_status = "FAILED_VERIFICATION" if tamper_detected else "VERIFIED_PROVENANCE"

print()
print("=" * 70)
print("CASE 2: TAMPERED COPY DEMONSTRATION")
print("=" * 70)
print("Tampered asset:", target_asset["asset_name"])
print("Original file:", target_asset["relative_path"])
print("Tampered copy:", tampered_path)
print("Expected SHA-256:", expected_hash)
print("Tampered SHA-256:", tampered_hash)
print("Hash match:", expected_hash == tampered_hash)
print("Verification result:", failed_status)
print("=" * 70)
