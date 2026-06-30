# MediFoodShield Reproducibility Guide

## Environment

The prototype was developed in Google Colab using Python.

Install dependencies:

```bash
pip install -r requirements.txt
```

For OCR, Tesseract is also required:

```bash
apt-get update
apt-get install -y tesseract-ocr
```

## Required Files

The following files are needed to run the current cleaned prototype:

```text
data_processed/ddid_evidence_lookup_guard_table.csv
models/medsafe_gate_v1_calibrated_linearsvc.joblib
security/demo_hmac_key_DO_NOT_SHARE.key
security/security_manifest_v1_signed.json
src/core/medifood_engine.py
src/ocr/rxocr_guard.py
apps/app_gradio_rxocr.py
scripts/test_engine.py
```

## Backend Test

Run:

```bash
python scripts/test_engine.py
```

Expected examples:

```text
Ibuprofen + Ginkgo Biloba -> Avoid
Omeprazole + Grapefruit -> Use caution
Atorvastatin + High-Fat Meal -> Use caution
RandomDrugXYZ + RandomFoodXYZ -> Insufficient evidence
```

## App Test

Run:

```bash
python apps/app_gradio_rxocr.py
```

Test with a synthetic prescription image containing:

```text
Ibuprofen 200 mg tablet
Omeprazole 20 mg capsule
Atorvastatin 10 mg tablet
```

Expected OCR candidates:

```text
Ibuprofen
Omeprazole
Atorvastatin
```

Then test:

```text
Ibuprofen + Ginkgo Biloba -> Avoid
Omeprazole + Grapefruit -> Use caution
Atorvastatin + High-Fat Meal -> Use caution
```

## Security Reproducibility

The implemented software security prototype protects:

- DDID lookup table
- trained model file
- inference policy
- output logs
- signed recommendation outputs

The current attack simulation includes:

- DDID lookup table tampering
- model file tampering
- policy modification / rollback
- output log tampering
- displayed recommendation output tampering

Current result:

```text
5/5 implemented tampering attacks detected
```

## Notes for Raspberry Pi

Before Raspberry Pi testing:

- copy the cleaned project folder to Raspberry Pi,
- install dependencies,
- verify Tesseract installation,
- rerun backend test,
- rerun Gradio app,
- measure latency and memory on device,
- replace demo HMAC key with device-bound or hardware-rooted key if available.
