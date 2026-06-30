import os
import io
import re
import fitz
import pandas as pd
import pytesseract

from PIL import Image, ImageOps, ImageFilter
from rapidfuzz import process, fuzz

from src.utils.text_utils import normalize_name
from src.security.security_utils import sha256_file

class RxOCRGuard:
    def __init__(self, drug_norm_to_display, score_cutoff=85):
        self.drug_norm_to_display = drug_norm_to_display
        self.drug_norm_choices = list(drug_norm_to_display.keys())
        self.score_cutoff = score_cutoff

    def preprocess_image_for_ocr(self, path):
        img = Image.open(path).convert("L")

        w, h = img.size
        img = img.resize((w * 3, h * 3))

        img = ImageOps.autocontrast(img)
        img = img.filter(ImageFilter.SHARPEN)
        img = img.point(lambda x: 0 if x < 160 else 255, "1")

        return img

    def extract_text_from_image(self, path):
        try:
            img = self.preprocess_image_for_ocr(path)
            config = "--oem 3 --psm 6"
            text = pytesseract.image_to_string(img, config=config)
            return text.strip(), "Image OCR using Tesseract with preprocessing"
        except Exception as e:
            return f"Image OCR error: {e}", "Extraction error"

    def extract_text_from_pdf(self, path):
        text_parts = []

        try:
            doc = fitz.open(path)

            for page in doc:
                page_text = page.get_text()
                if page_text:
                    text_parts.append(page_text)

            text = "\n".join(text_parts).strip()

            if len(text) > 20:
                return text, "PDF selectable text extraction"

            ocr_parts = []

            for page in doc:
                pix = page.get_pixmap(dpi=200)
                img_bytes = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_bytes))
                ocr_text = pytesseract.image_to_string(img)
                ocr_parts.append(ocr_text)

            return "\n".join(ocr_parts).strip(), "PDF image OCR using Tesseract"

        except Exception as e:
            return f"OCR/PDF extraction error: {e}", "Extraction error"

    def extract_prescription_text(self, file_path):
        if file_path is None:
            return "", "No file uploaded", ""

        path = str(file_path)
        ext = os.path.splitext(path)[1].lower()

        file_hash = sha256_file(path)

        if ext == ".pdf":
            text, method = self.extract_text_from_pdf(path)
        elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"]:
            text, method = self.extract_text_from_image(path)
        else:
            text = "Unsupported file type. Please upload PDF, PNG, JPG, JPEG, WEBP, BMP, or TIFF."
            method = "Unsupported file type"

        return text, method, file_hash

    def clean_ocr_for_matching(self, text):
        text = str(text)
        text = text.replace("\n", " ")

        text = re.sub(
            r"\b\d+(\.\d+)?\s*(mg|mcg|g|ml|tablet|tablets|tab|tabs|capsule|capsules|cap|caps)\b",
            " ",
            text,
            flags=re.I
        )

        text = re.sub(
            r"\b(take|one|once|twice|daily|night|morning|evening|before|after|food|needed|as|prn|tablet|capsule)\b",
            " ",
            text,
            flags=re.I
        )

        text = re.sub(r"[^A-Za-z0-9\s\-]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def detect_medications_from_text(self, ocr_text, max_results=8):
        cleaned = self.clean_ocr_for_matching(ocr_text)
        cleaned_norm = normalize_name(cleaned)

        detected = []

        for norm_name, display_name in self.drug_norm_to_display.items():
            if len(norm_name) >= 4 and norm_name in cleaned_norm:
                detected.append({
                    "Drug_Name": display_name,
                    "match_type": "exact_substring",
                    "score": 100.0,
                    "matched_text": norm_name
                })

        chunks = []

        raw_lines = str(ocr_text).splitlines()

        for line in raw_lines:
            line_clean = self.clean_ocr_for_matching(line)
            line_clean = normalize_name(line_clean)

            if len(line_clean) >= 4:
                chunks.append(line_clean)

        words = self.clean_ocr_for_matching(ocr_text).split()

        for n in [1, 2, 3]:
            for i in range(max(0, len(words) - n + 1)):
                phrase = " ".join(words[i:i+n])
                phrase_norm = normalize_name(phrase)

                if len(phrase_norm) >= 4:
                    chunks.append(phrase_norm)

        seen_chunks = set()

        for chunk_norm in chunks:
            if chunk_norm in seen_chunks:
                continue

            seen_chunks.add(chunk_norm)

            if len(chunk_norm) < 5:
                continue

            best_match = process.extractOne(
                chunk_norm,
                self.drug_norm_choices,
                scorer=fuzz.WRatio
            )

            if best_match is None:
                continue

            match_norm, score, _ = best_match

            if len(match_norm) < 6:
                continue

            bad_context_words = ["synthetic", "prescription", "patient", "test", "user", "medication"]

            if any(word in chunk_norm for word in bad_context_words):
                continue

            if score >= self.score_cutoff:
                detected.append({
                    "Drug_Name": self.drug_norm_to_display[match_norm],
                    "match_type": "fuzzy",
                    "score": round(float(score), 2),
                    "matched_text": chunk_norm
                })

        if not detected:
            return pd.DataFrame(columns=["Drug_Name", "match_type", "score", "matched_text"])

        detected_df = pd.DataFrame(detected)

        detected_df = detected_df.sort_values(
            ["score", "match_type", "Drug_Name"],
            ascending=[False, True, True]
        )

        detected_df = detected_df.drop_duplicates(
            subset=["Drug_Name"],
            keep="first"
        )

        detected_df["match_rank"] = detected_df["match_type"].map({
            "exact_substring": 0,
            "fuzzy": 1
        }).fillna(2)

        detected_df = detected_df.sort_values(
            ["match_rank", "score"],
            ascending=[True, False]
        )

        detected_df = detected_df.head(max_results).reset_index(drop=True)

        return detected_df[["Drug_Name", "match_type", "score", "matched_text"]]

    def run_ocr_and_detect(self, file_path):
        text, method, file_hash = self.extract_prescription_text(file_path)
        detected_df = self.detect_medications_from_text(text)

        detected_meds = detected_df["Drug_Name"].tolist() if len(detected_df) > 0 else []

        status = f"""
### OCR Status

- **Extraction method:** {method}
- **Prescription file hash:** `{file_hash[:32]}...` if available
- **Detected medications:** {len(detected_meds)}

Please review and confirm the detected medication before screening.
"""

        default_med = detected_meds[0] if len(detected_meds) > 0 else None

        return text, detected_df, detected_meds, default_med, status
