# MediFoodShield

MediFoodShield is a research prototype for medication-aware food-risk screening with trustworthy AI and software security verification.

The prototype combines:

- DDID evidence lookup
- MedSafe-GATE v1 AI model with safety gate
- input coverage guard
- prescription OCR using RxOCR-Guard
- user-confirmed medication selection
- food/herb/drink selection
- HMAC-signed recommendation output
- SHA-256/HMAC-based security manifest
- tamper detection experiments

## Important Disclaimer

This research prototype is intended for medication-aware food-risk screening using curated public knowledge sources. It is not a substitute for advice from physicians, pharmacists, or registered dietitians.

The system does not claim that a food-medication pair is clinically safe. The output label is:

**No known interaction in selected source**

not “safe.”

## Main Output Labels

- Avoid
- Use caution
- No known interaction in selected source
- Insufficient evidence

## Current Implemented Workflow

1. Upload prescription PDF/image or manually select a medication.
2. RxOCR-Guard extracts text from the uploaded file.
3. Medication names are detected using DDID drug vocabulary and fuzzy matching.
4. User confirms the detected medication.
5. User selects a food/herb/drink.
6. MediFoodShield checks DDID exact-pair evidence first.
7. If exact evidence is unavailable but both entities are known, MedSafe-GATE v1 model branch runs.
8. If one or both entities are outside DDID coverage, the system returns Insufficient evidence.
9. Final recommendation output is signed and security verification fields are shown.

## Clean Code Structure

```text
MediFoodShield/
├── apps/
│   └── app_gradio_rxocr.py
├── data_processed/
├── models/
├── security/
├── src/
│   ├── core/
│   │   └── medifood_engine.py
│   ├── ocr/
│   │   └── rxocr_guard.py
│   ├── security/
│   │   └── security_utils.py
│   └── utils/
│       └── text_utils.py
└── scripts/
    └── test_engine.py
```

## Run Backend Test

From inside the project folder:

```bash
python scripts/test_engine.py
```

Expected test outputs:

```text
Ibuprofen + Ginkgo Biloba -> Avoid
Omeprazole + Grapefruit -> Use caution
Atorvastatin + High-Fat Meal -> Use caution
RandomDrugXYZ + RandomFoodXYZ -> Insufficient evidence
```

## Run Gradio App

```bash
python apps/app_gradio_rxocr.py
```

In Google Colab, the app cell will continue running while the Gradio app is active.

## Current Paper-Ready Results

AI safety result:

- Balanced AI baseline false-safe count: 128
- Balanced AI baseline false-safe rate: 5.29%
- MedSafe-GATE v1 strict-screening false-safe count: 15
- MedSafe-GATE v1 strict-screening false-safe rate: 0.62%

Security result:

- Simulated tampering attacks detected: 5/5
- Attack detection rate in implemented tests: 100%

Runtime result:

- Full manifest verification mean time: 48.539 ms
- Sign one recommendation output mean time: 0.030 ms
- Fast exact DDID lookup + signing: about 0.057 ms
- Known-entity model branch + signing: about 3.614 ms

## Limitations

- This is not a clinical validation study.
- DDID coverage limits what the system can detect.
- OCR requires user confirmation.
- The HMAC key is currently a demo software key.
- Raspberry Pi hardware-rooted testing is still required.
