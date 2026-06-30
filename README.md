# iMediFood-Shield

**iMediFood-Shield** is a secure edge AI research prototype for food--medication interaction screening. It combines DDID-based evidence lookup, safety-gated AI prediction, prescription OCR with user confirmation, input coverage checking, signed recommendation outputs, tamper-evident verification, and Raspberry Pi edge validation.

The main goal of iMediFood-Shield is to reduce unsafe food--medication screening outputs, especially **false-safe predictions**, where a risky food--medication pair is incorrectly shown as having no known interaction.

---

## Important Medical Disclaimer

iMediFood-Shield is a **research prototype**. It is not a medical device and should not be used as a substitute for advice from physicians, pharmacists, registered dietitians, or other qualified healthcare professionals.

The system does **not** claim that a food--medication pair is clinically safe. The output label:

```text
No known interaction in selected source
```

means that no interaction was found in the selected evidence source used by the prototype. It does **not** mean that the pair is universally safe.

---

## What This Repository Contains

This repository contains the implementation, application files, processed data, model artifacts, security verification files, Raspberry Pi validation scripts, and paper-ready results for the iMediFood-Shield prototype.

The prototype includes:

- DDID-based exact evidence lookup
- MedSafe-GATE v1 safety-gated AI screening
- RxOCR-Guard prescription OCR and user confirmation
- CoverageGuard for unsupported medication or food/herb/drink inputs
- SHA-256 file integrity checking
- HMAC-SHA256 signed security manifest
- HMAC-SHA256 signed recommendation outputs
- Tampering attack simulation
- Fast secured inference latency testing
- Raspberry Pi edge validation

---

## Main Output Labels

iMediFood-Shield returns one of the following user-facing outputs:

```text
Avoid
Use caution
No known interaction in selected source
Insufficient evidence
```

### Label Meaning

| Output Label | Meaning |
|---|---|
| `Avoid` | The selected evidence source indicates a harmful or high-risk interaction. |
| `Use caution` | The selected evidence source indicates an interaction effect or uncertainty that should not be treated as safe. |
| `No known interaction in selected source` | No interaction was found in the selected source. This does not mean clinically safe. |
| `Insufficient evidence` | One or both inputs are outside the supported DDID-derived vocabulary. |

---

## Current Implemented Workflow

1. The user uploads a prescription PDF/image or manually selects a medication.
2. RxOCR-Guard extracts prescription text when a file is provided.
3. Candidate medication names are matched against the DDID-derived medication vocabulary.
4. The user confirms the correct medication before screening.
5. The user selects a food, herb, drink, or diet-related item.
6. iMediFood-Shield checks exact DDID-supported evidence first.
7. If an exact pair exists, the evidence-derived recommendation is returned.
8. If no exact pair exists but both inputs are covered, MedSafe-GATE v1 runs.
9. If one or both inputs are outside DDID coverage, CoverageGuard returns `Insufficient evidence`.
10. The final recommendation output is signed.
11. Security verification checks protected files and recommendation-output integrity.

---

## Repository Structure

```text
iMediFood-Shield/
├── .gradio/
│   └── Gradio app runtime/config files
│
├── apps/
│   └── app_gradio_rxocr.py
│       Gradio application with prescription OCR and screening interface
│
├── data_raw/
│   └── Raw or original data files used before processing
│
├── data_processed/
│   └── Processed DDID-derived tables, lookup files, and vocabulary files
│
├── docs/
│   └── Documentation, notes, and supporting paper files
│
├── important_results/
│   └── Paper-ready figures, tables, logs, and final important outputs
│
├── models/
│   └── Trained MedSafe-GATE v1 model/vectorizer/calibration artifacts
│
├── results/
│   └── General experiment outputs and generated result files
│
├── rpi_env/
│   └── Local Python virtual environment folder
│
├── scripts/
│   ├── test_engine.py
│   ├── rpi_system_info.py
│   ├── rpi_security_refresh.py
│   ├── show_verified_failed_demo.py
│   └── rpi_validation_timing.py
│
├── security/
│   └── Security manifests, signed records, hashes, and verification files
│
├── src/
│   ├── core/
│   │   └── medifood_engine.py
│   ├── ocr/
│   │   └── rxocr_guard.py
│   ├── security/
│   │   └── security_utils.py
│   └── utils/
│       └── text_utils.py
│
├── figma_ddid_food_herb_list.json
├── figma_ddid_food_herb_list.txt
├── medifood.py
├── requirements.txt
├── synthetic_prescription_test.png
└── README.md
```

---

## Folder Details

### `apps/`

Contains the Gradio user interface.

Main file:

```text
apps/app_gradio_rxocr.py
```

Use this file to launch the interactive iMediFood-Shield app.

---

### `src/`

Contains the main source code for the screening engine, OCR layer, security utilities, and text normalization.

Expected modules:

```text
src/core/medifood_engine.py
src/ocr/rxocr_guard.py
src/security/security_utils.py
src/utils/text_utils.py
```

---

### `data_raw/`

Contains original or raw data files before processing.

---

### `data_processed/`

Contains processed DDID-derived files such as lookup tables, cleaned data, vocabulary files, and pair-level screening tables.

This folder is required for running the prototype.

---

### `models/`

Contains trained model artifacts for MedSafe-GATE v1.

This folder is required for AI model-branch prediction.

---

### `security/`

Contains security manifests, hash files, signed records, and verification outputs.

This folder is required for tamper-evident verification.

---

### `scripts/`

Contains backend tests, Raspberry Pi validation scripts, timing scripts, and security validation scripts.

Important scripts:

```text
scripts/test_engine.py
scripts/rpi_system_info.py
scripts/rpi_security_refresh.py
scripts/show_verified_failed_demo.py
scripts/rpi_validation_timing.py
```

---

### `important_results/`

Contains paper-ready figures, result tables, terminal logs, and Raspberry Pi validation results.

---

### `synthetic_prescription_test.png`

A sample synthetic prescription image for testing RxOCR-Guard.

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/chakravarthulaharsha/iMediFood-Shield.git
cd iMediFood-Shield
```

---

### 2. Create a Python Virtual Environment

For Linux, macOS, or Raspberry Pi:

```bash
python -m venv rpi_env
source rpi_env/bin/activate
```

For Windows:

```bash
python -m venv rpi_env
rpi_env\Scripts\activate
```

---

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## OCR Requirement

RxOCR-Guard uses Tesseract OCR.

### Ubuntu / Raspberry Pi OS

```bash
sudo apt update
sudo apt install -y tesseract-ocr
```

### macOS

```bash
brew install tesseract
```

### Windows

Install Tesseract OCR from the official Windows installer and make sure the Tesseract executable is added to the system PATH.

After installation, check:

```bash
tesseract --version
```

---

## How to Run the Backend Test

From the project root:

```bash
python scripts/test_engine.py
```

Expected example outputs:

```text
Ibuprofen + Ginkgo Biloba -> Avoid
Omeprazole + Grapefruit -> Use caution
Atorvastatin + High-Fat Meal -> Use caution
RandomDrugXYZ + RandomFoodXYZ -> Insufficient evidence
```

This checks:

- exact DDID lookup
- cautionary recommendation output
- coverage-guard blocking for unsupported inputs
- signed output behavior

---

## How to Run the Gradio App

From the project root:

```bash
python apps/app_gradio_rxocr.py
```

Then open the local Gradio URL printed in the terminal.

In Google Colab or notebook environments, the app cell will continue running while the Gradio interface is active.

---

## How to Test Prescription OCR

Use the provided synthetic prescription image:

```text
synthetic_prescription_test.png
```

Steps:

1. Run the Gradio app.
2. Upload `synthetic_prescription_test.png`.
3. Let RxOCR-Guard extract possible medication names.
4. Confirm the correct medication.
5. Select a food/herb/drink.
6. Generate the recommendation.

The medication extracted from OCR must be confirmed by the user before it is used for screening.

---

## Quick Start Commands

For a new user, run:

```bash
git clone https://github.com/chakravarthulaharsha/iMediFood-Shield.git
cd iMediFood-Shield

python -m venv rpi_env
source rpi_env/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

python scripts/test_engine.py
python apps/app_gradio_rxocr.py
```

For Windows:

```bash
git clone https://github.com/chakravarthulaharsha/iMediFood-Shield.git
cd iMediFood-Shield

python -m venv rpi_env
rpi_env\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt

python scripts/test_engine.py
python apps/app_gradio_rxocr.py
```

---

## Example Demo Cases

The prototype can be tested with these example cases:

| Medication | Food/Herb/Drink | Expected Output |
|---|---|---|
| Ibuprofen | Ginkgo Biloba | Avoid |
| Atorvastatin | Grapefruit | Avoid |
| Warfarin | Cranberry | Avoid |
| Simvastatin | Grapefruit | Avoid |
| Simvastatin | Green Tea | Avoid |
| Ibuprofen | Alcohol | Use caution |
| Omeprazole | Grapefruit | Use caution |
| Omeprazole | Kale | Use caution |
| Atorvastatin | High-Fat Meal | Use caution |
| RandomDrugXYZ | RandomFoodXYZ | Insufficient evidence |

---

## Raspberry Pi Validation

The Raspberry Pi validation scripts should be run from the project root on the Raspberry Pi.

Activate the virtual environment:

```bash
cd /home/pi/Desktop/MediFoodShield
source rpi_env/bin/activate
```

If the repository folder name is different, use that folder path instead.

---

### 1. Check Raspberry Pi System Information

```bash
python scripts/rpi_system_info.py | tee paper_ready_results/raspberry_pi/rpi_system_info.txt
```

This records Raspberry Pi OS, Python version, CPU, RAM, and architecture information.

---

### 2. Refresh Raspberry Pi Security Manifest

```bash
python scripts/rpi_security_refresh.py | tee paper_ready_results/raspberry_pi/rpi_security_refresh_log.txt
```

Expected result:

```text
Verification result: VERIFIED_PROVENANCE
Protected assets: 5
Missing assets: 0
Attack detection: 5/5
Attack detection rate: 100.0%
```

---

### 3. Show Verified and Failed Verification Demo

```bash
python scripts/show_verified_failed_demo.py | tee paper_ready_results/raspberry_pi/rpi_verified_failed_command_demo.txt
```

Expected behavior:

```text
CASE 1: ORIGINAL RASPBERRY PI DEPLOYMENT
Verification result: VERIFIED_PROVENANCE

CASE 2: TAMPERED COPY DEMONSTRATION
Verification result: FAILED_VERIFICATION
```

This confirms that the original protected state verifies successfully and the tampered copy fails verification.

---

### 4. Run Raspberry Pi Validation Timing

```bash
python scripts/rpi_validation_timing.py | tee paper_ready_results/raspberry_pi/rpi_validation_timing_terminal_log.txt
```

Expected paper-ready timing summary:

```text
runs: 30
verified_status: VERIFIED_PROVENANCE
failed_status: FAILED_VERIFICATION
protected_assets: 5

verified_mean_ms: 167.79
verified_std_ms: 0.137
verified_min_ms: 167.504
verified_max_ms: 168.05

failed_mean_ms: 159.709
failed_std_ms: 0.436
failed_min_ms: 159.093
failed_max_ms: 161.527
```

Generated files:

```text
paper_ready_results/raspberry_pi/rpi_validation_timing.csv
paper_ready_results/raspberry_pi/rpi_validation_timing_summary.txt
paper_ready_results/raspberry_pi/rpi_validation_timing_terminal_log.txt
```

---

## Paper-Ready Dataset Result

The DDID-derived dataset formation produced:

| Dataset Stage | Count |
|---|---:|
| Cleaned row-level DDID records | 23,950 |
| Final pair-level medication--food/herb records | 17,693 |

The pair-level dataset uses safety-priority aggregation:

```text
Avoid > Use caution > No known interaction in selected source
```

This means that when the same medication--food/herb pair has conflicting records, the strongest safety label is preserved.

---

## Paper-Ready AI Result

The main AI result is that MedSafe-GATE v1 reduces false-safe outputs while keeping strong accuracy.

| Model / Mode | False-Safe Count | False-Safe Rate |
|---|---:|---:|
| Balanced AI baseline | 128 | 5.29% |
| Calibrated balanced mode | 96 | 3.97% |
| MedSafe-GATE v1 balanced-safety threshold 0.6 | 47 | 1.94% |
| MedSafe-GATE v1 strict-screening threshold 0.7 | 15 | 0.62% |

Main reported AI values:

```text
Balanced AI baseline accuracy: 91.86%
Balanced AI baseline false-safe rate: 5.29%

MedSafe-GATE v1 strict-screening accuracy: 90.99%
MedSafe-GATE v1 strict-screening false-safe rate: 0.62%
```

Interpretation:

The balanced AI baseline gives strong overall accuracy, but it still produces false-safe errors. The strict MedSafe-GATE v1 mode is more conservative. It shifts uncertain no-interaction predictions toward `Use caution`, reducing the safety-critical false-safe rate from 5.29% to 0.62%.

---

## Paper-Ready Security Attack Detection Result

The implemented tampering tests target files and outputs that can influence the recommendation pipeline.

| Attack Type | Detection Result |
|---|---|
| DDID lookup table tampering | Detected |
| Model file tampering | Detected |
| Policy modification / rollback | Detected |
| Output log tampering | Detected |
| Displayed recommendation tampering | Detected |

Summary:

```text
Implemented tampering attacks detected: 5/5
Attack detection rate in implemented tests: 100%
```

This result only applies to the implemented attack simulations. It does not imply complete protection against every possible cybersecurity attack.

---

## Paper-Ready Fast Secured Inference Result

| Screening Path | Mean Time |
|---|---:|
| Exact DDID lookup: Ibuprofen + Ginkgo Biloba | 0.063 ms |
| Exact DDID lookup: Atorvastatin + High-Fat Meal | 0.054 ms |
| Coverage guard | 0.052 ms |
| Model branch | 2.940 ms |

Interpretation:

Exact DDID lookup and coverage-guard paths are very fast because they do not require model inference. The model branch takes longer but still remains in the millisecond range.

---

## Paper-Ready Security Runtime Result

```text
Full manifest verification mean time: 48.539 ms
Recommendation signing mean time: 0.030 ms
Fast exact DDID lookup + signing: about 0.057 ms
Known-entity model branch + signing: about 3.614 ms
```

---

## Paper-Ready Raspberry Pi Edge Result

The Raspberry Pi validation confirms that tamper-evident verification can run locally on edge hardware.

Raspberry Pi system summary:

```text
CPU cores: 4
Architecture: ARMv7l
Model name: Cortex-A72
RAM: approximately 3.75 GB
```

Validation timing over 30 runs:

| Verification Case | Mean | Std | Min | Max |
|---|---:|---:|---:|---:|
| Verified provenance | 167.79 ms | 0.137 ms | 167.504 ms | 168.05 ms |
| Failed verification | 159.709 ms | 0.436 ms | 159.093 ms | 161.527 ms |

---

## Security Design

iMediFood-Shield protects the following assets:

```text
DDID-derived evidence lookup table
Trained model file
Inference policy file
Label mapping files
Dataset summary files
Recommendation logs
Signed recommendation records
```

The prototype uses:

```text
SHA-256 for file hashing
HMAC-SHA256 for manifest signing
HMAC-SHA256 for recommendation-output signing
Signed manifest verification
Signed recommendation-output verification
```

A successful verification returns:

```text
VERIFIED_PROVENANCE
```

A failed verification returns:

```text
FAILED_VERIFICATION
```

---

## What to Run First

For normal local testing, run in this order:

```bash
git clone https://github.com/chakravarthulaharsha/iMediFood-Shield.git
cd iMediFood-Shield
python -m venv rpi_env
source rpi_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python scripts/test_engine.py
python apps/app_gradio_rxocr.py
```

For Raspberry Pi validation, run:

```bash
source rpi_env/bin/activate
python scripts/rpi_system_info.py
python scripts/rpi_security_refresh.py
python scripts/show_verified_failed_demo.py
python scripts/rpi_validation_timing.py
```

---

## Troubleshooting

### Problem: `ModuleNotFoundError`

Make sure the virtual environment is activated and dependencies are installed:

```bash
source rpi_env/bin/activate
pip install -r requirements.txt
```

For Windows:

```bash
rpi_env\Scripts\activate
pip install -r requirements.txt
```

---

### Problem: OCR does not work

Check whether Tesseract is installed:

```bash
tesseract --version
```

Install it if missing:

```bash
sudo apt install -y tesseract-ocr
```

---

### Problem: App does not open

Run:

```bash
python apps/app_gradio_rxocr.py
```

Then copy the local Gradio URL from the terminal into a browser.

---

### Problem: Security verification fails

A failed verification means one or more protected files, signed outputs, or manifest records may not match the expected signed state.

Run:

```bash
python scripts/rpi_security_refresh.py
```

Only refresh the manifest when trusted files were intentionally changed.

---

### Problem: `Insufficient evidence`

This means the medication or food/herb/drink is outside the DDID-derived vocabulary used by the prototype. It is not a code error. It is the intended safe behavior of CoverageGuard.

---

## Limitations

- This is not a clinical validation study.
- The system depends on DDID-derived coverage.
- `No known interaction in selected source` does not mean clinically safe.
- OCR output must be confirmed by the user.
- The current HMAC key is a software demonstration key.
- The implemented attacks are controlled prototype tests and do not cover all possible adversarial scenarios.
- Clinical deployment would require expert review, clinical validation, usability testing, regulatory review, and stronger key protection.

---

## Recommended Citation

If this repository is used for research, cite the related iMediFood-Shield work when available.

```bibtex
@misc{imedifoodshield2026,
  title        = {{iMediFood-Shield: Secure Edge AI for Food and Medication Interaction Screening}},
  author       = {Chakravarthula, Sai Sri Harsha and Siripurapu, Indira Devi and Rachakonda, Laavanya and Mohanty, Saraju P. and Kougianos, Elias},
  year         = {2026},
  note         = {Research prototype}
}
```

---

## Authors

- Sai Sri Harsha Chakravarthula
- Indira Devi Siripurapu
- Laavanya Rachakonda
- Saraju P. Mohanty
- Elias Kougianos

---

## Project Status

iMediFood-Shield is an active research prototype for secure edge AI food--medication interaction screening. The current implementation supports evidence lookup, safety-gated AI inference, prescription OCR confirmation, coverage guarding, recommendation signing, tamper detection, fast secured inference testing, and Raspberry Pi edge validation.
