import json
import re
import ftfy
import fitz
from pathlib import Path
import easyocr

from src.config import INTERIM_DATA_DIR, RAW_DATA_DIR

SLOVAK_ALPHABET = set("ľščťžýáíéúäôňďĺŕ")
_easyocr_reader = None


def get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None:
        print("🧠 [Initialization] Loading EasyOCR neural network weights (SK+EN)...")
        _easyocr_reader = easyocr.Reader(['sk', 'en'], gpu=True)
    return _easyocr_reader


def clean_document_vulnerabilities(text: str) -> str:
    # 1. STRIP MULTILINGUAL PUBLICATION HEADERS (Compiles across newlines via re.DOTALL)
    pub_pattern = r"(Official Journal of the European Union\s+EN\s+L series.*?\d+/\d+|Úradný vestník Európskej únie\s+SK\s+Séria L.*?\d+/\d+|EN\s+OJ\s+L,\s+\d{1,2}\.\d{1,2}\.\d{4}\s+\d+/\d+)"
    text = re.sub(pub_pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # 2. STRIP ELI URL HEADERS AND RUNNING BOUNDARY STRIKES
    eli_pattern = r"ELI:\s+http://data\.europa\.eu/eli/reg/\S+"
    text = re.sub(eli_pattern, "", text)

    # 3. CLEAN TABLE OF CONTENTS DOT PADDING
    text = re.sub(r"\.{4,}", "...", text)

    # 4. FIX THE INLINE SPLITTER SEPARATOR ALIGNMENT BUG
    text = re.sub(r"(?<!\n)(Article\s+\d+)", r"\n\1", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<!\n)(Článok\s+\d+)", r"\n\1", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<!\n)(§\s+\d+)", r"\n\1", text)

    return text


def clean_extra_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def group_broken_paragraphs(text: str) -> str:
    lines = text.split("\n")
    processed_lines = []

    list_tag_pattern = r"^\s*([a-z0-9]\)|➪|➢|\(\d+\))"

    for line in lines:
        stripped = line.strip()

        if (not stripped
                or stripped.startswith("#")
                or stripped.startswith("-")
                or stripped.startswith("*")
                or stripped.startswith("|")
                or stripped.lower().startswith("article")
                or stripped.lower().startswith("článok")
                or stripped.startswith("§")
                or re.match(list_tag_pattern, stripped, re.IGNORECASE)):
            processed_lines.append(line)
            continue

        if processed_lines and not re.search(r"[.!:;]$", processed_lines[-1].strip()):
            processed_lines[-1] = processed_lines[-1].rstrip() + " " + stripped
        else:
            processed_lines.append(line)

    return "\n".join(processed_lines)


def detect_language(text: str) -> str:
    if not text:
        return "en"
    total_chars = len(text)
    sk_chars = sum(1 for c in text.lower() if c in SLOVAK_ALPHABET)
    sk_ratio = (sk_chars / total_chars) * 100
    return "sk" if sk_ratio >= 0.5 else "en"


def clean_text_pipeline(text: str) -> str:
    text = ftfy.fix_text(text)
    text = clean_document_vulnerabilities(text)
    text = group_broken_paragraphs(text)
    text = clean_extra_whitespace(text)
    return text


def process_documents(raw_dir: Path, interim_dir: Path):
    files = list(raw_dir.glob("*.pdf"))
    print(f"🚀 Ingesting {len(files)} legal documents...")

    for pdf_file in files:
        try:
            with fitz.open(str(pdf_file)) as doc:
                final_chunks = []

                print(f"📖 Analyzing layout for: {pdf_file.name}")
                for page_num, page in enumerate(doc):
                    page_text = page.get_text()

                    if len(page_text.strip()) < 50:
                        print(f"  📷 Page {page_num + 1}/{len(doc)} looks like an image. Running EasyOCR...")
                        pix = page.get_pixmap(dpi=150)
                        img_bytes = pix.tobytes("png")

                        reader = get_easyocr_reader()
                        ocr_result = reader.readtext(img_bytes, detail=0)
                        page_text = "\n".join(ocr_result)

                    final_chunks.append(page_text)

                combined_text = "\n\n".join(final_chunks)

            cleaned_text = clean_text_pipeline(combined_text)
            detected_lang = detect_language(cleaned_text)

            data_object = {
                "source": pdf_file.name,
                "content": cleaned_text,
                "metadata": {
                    "type": "legal_text",
                    "language": detected_lang,
                    "pipeline": "PyMuPDF + EasyOCR + ftfy"
                }
            }

            output_file = interim_dir / f"{pdf_file.stem}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data_object, f, ensure_ascii=False, indent=2)

            print(f"✅ Completed: {pdf_file.name} (Language: {detected_lang.upper()})")

        except Exception as e:
            print(f"❌ Error processing {pdf_file.name}: {e}")


if __name__ == "__main__":
    process_documents(RAW_DATA_DIR, INTERIM_DATA_DIR)