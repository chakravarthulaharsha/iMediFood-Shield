import os
import json
import hmac
import hashlib

def sha256_text(text):
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()

def sha256_file(path, chunk_size=8192):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def canonical_json_bytes(obj):
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")

def hmac_sign_record(record_body, key):
    return hmac.new(
        key,
        canonical_json_bytes(record_body),
        hashlib.sha256
    ).hexdigest()

def verify_signed_record(signed_record, key):
    record_body = signed_record["record_body"]
    stored_signature = signed_record["record_signature_hmac_sha256"]
    recomputed_signature = hmac_sign_record(record_body, key)
    return hmac.compare_digest(stored_signature, recomputed_signature)
