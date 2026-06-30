import json
import gradio as gr
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.core.medifood_engine import MediFoodShieldEngine
from src.ocr.rxocr_guard import RxOCRGuard

engine = MediFoodShieldEngine(BASE_DIR)
rxocr = RxOCRGuard(engine.drug_norm_to_display, score_cutoff=85)

def run_ocr_and_detect_ui(file_path):
    text, detected_df, detected_meds, default_med, status = rxocr.run_ocr_and_detect(file_path)

    choices = detected_meds if detected_meds else engine.drug_choices

    return (
        text,
        detected_df,
        gr.update(choices=choices, value=default_med),
        status
    )

def format_recommendation(result, signed_record):
    label = result.get("recommendation_label", "Insufficient evidence")
    source = result.get("source", "")
    decision_source = result.get("final_decision_source", "")
    signature = signed_record["record_signature_hmac_sha256"]
    output_hash = signed_record["record_body"]["output_hash"]

    if label == "Avoid":
        recommendation_text = (
            "### Recommendation: AVOID\n\n"
            "The selected source indicates a potentially harmful or avoid-level interaction."
        )
    elif label == "Use caution":
        recommendation_text = (
            "### Recommendation: USE CAUTION\n\n"
            "The selected source or model indicates that caution is needed."
        )
    elif label == "No known interaction in selected source":
        recommendation_text = (
            "### Recommendation: NO KNOWN INTERACTION IN SELECTED SOURCE\n\n"
            "This does not mean clinically safe. It only means no known interaction was selected by this prototype/source branch."
        )
    else:
        recommendation_text = (
            "### Recommendation: INSUFFICIENT EVIDENCE\n\n"
            "The system does not have enough source coverage to make a recommendation."
        )

    evidence_text = f"""
### Evidence / Decision Source

- **Drug:** {result.get("drug_name_input", "")}
- **Food/Herb/Drink:** {result.get("food_herb_name_input", "")}
- **Decision source:** {decision_source}
- **Branch:** {source}
- **Found in DDID exact lookup:** {result.get("found_in_ddid", False)}
- **Coverage guard applied:** {result.get("coverage_guard_applied", False)}
- **Evidence row count:** {result.get("evidence_row_count", "")}
- **Effect:** {result.get("effect_clean", "")}
- **DDID effects:** {result.get("ddid_effects_all", "")}
- **Conclusion:** {result.get("Conclusion", "")}
- **Reference:** {result.get("Reference", "")}
- **DOI:** {result.get("DOI", "")}
"""

    if result.get("source") == "MedSafe-GATE v1 model branch":
        evidence_text += f"""

### Model probabilities

- **Avoid:** {result.get("prob_avoid", 0):.4f}
- **Use caution:** {result.get("prob_use_caution", 0):.4f}
- **No known interaction:** {result.get("prob_no_known_interaction_in_selected_source", 0):.4f}
- **Safety gate applied:** {result.get("safety_gate_applied", False)}
"""

    security_text = f"""
### Security Verification

- **Output signed:** Yes
- **Signature method:** HMAC-SHA256 demo key
- **Output hash:** `{output_hash}`
- **Signature:** `{signature[:32]}...`
- **Model hash protected:** Yes
- **DDID lookup table hash protected:** Yes
- **Policy hash protected:** Yes
"""

    disclaimer = """
### Disclaimer

This research prototype is intended for medication-aware food-risk screening using curated public knowledge sources. It is not a substitute for advice from physicians, pharmacists, or registered dietitians.
"""

    raw_json = json.dumps(result, indent=2, ensure_ascii=False)

    return recommendation_text, evidence_text, security_text, disclaimer, raw_json

def check_food_medication(drug_name, food_herb_name, threshold):
    if not drug_name or not food_herb_name:
        return "Please select both a confirmed medication and a food/herb/drink.", "", "", "", ""

    result, signed_record = engine.recommend_and_sign(
        drug_name=drug_name,
        food_herb_name=food_herb_name,
        threshold=float(threshold)
    )

    return format_recommendation(result, signed_record)

with gr.Blocks(title="MediFoodShield RxOCR Demo") as demo:
    gr.Markdown(
        """
        # MediFoodShield RxOCR + Food-Risk Demo

        Upload a prescription PDF/image or manually select a medication.
        The user must confirm the detected medication before checking food-medication risk.
        """
    )

    gr.Markdown("## 1. Upload prescription and extract medication text")

    prescription_file = gr.File(
        label="Upload prescription PDF/image",
        file_types=[".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"],
        type="filepath"
    )

    extract_button = gr.Button("Extract medication names from prescription")

    ocr_status = gr.Markdown(label="OCR status")

    extracted_text = gr.Textbox(
        label="Extracted prescription text",
        lines=8
    )

    detected_table = gr.Dataframe(
        label="Detected medication candidates",
        headers=["Drug_Name", "match_type", "score", "matched_text"],
        interactive=False
    )

    gr.Markdown("## 2. Confirm medication and select food/herb/drink")

    with gr.Row():
        confirmed_medication = gr.Dropdown(
            choices=engine.drug_choices,
            label="Confirmed medication",
            value="Ibuprofen",
            allow_custom_value=True,
            filterable=True
        )

        food_dropdown = gr.Dropdown(
            choices=engine.food_choices,
            label="Select food / herb / drink",
            value="Ginkgo Biloba",
            allow_custom_value=True,
            filterable=True
        )

    threshold_slider = gr.Slider(
        minimum=0.5,
        maximum=0.95,
        value=0.7,
        step=0.05,
        label="Safety gate threshold"
    )

    check_button = gr.Button("Check food-medication risk")

    gr.Markdown("## 3. Recommendation, evidence, and security verification")

    recommendation_output = gr.Markdown(label="Recommendation")
    evidence_output = gr.Markdown(label="Evidence")
    security_output = gr.Markdown(label="Security")
    disclaimer_output = gr.Markdown(label="Disclaimer")
    raw_json_output = gr.Code(label="Raw result JSON", language="json")

    extract_button.click(
        fn=run_ocr_and_detect_ui,
        inputs=[prescription_file],
        outputs=[
            extracted_text,
            detected_table,
            confirmed_medication,
            ocr_status
        ]
    )

    check_button.click(
        fn=check_food_medication,
        inputs=[confirmed_medication, food_dropdown, threshold_slider],
        outputs=[
            recommendation_output,
            evidence_output,
            security_output,
            disclaimer_output,
            raw_json_output
        ]
    )

if __name__ == "__main__":
    demo.launch(share=True, debug=False)
