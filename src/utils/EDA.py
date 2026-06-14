import os
import pandas as pd
from pathlib import Path
from pypdf import PdfReader

from src.config import RAW_DATA_DIR

SLOVAK_ALPHABET = set("ľščťžýáíéúäôňďĺŕ")


def analyze_single_pdf(path: Path) -> dict:
    reader = PdfReader(path)
    full_text = ""
    empty_pages = 0

    for page in reader.pages:
        text = page.extract_text() or ""
        if len(text.strip()) < 15:
            empty_pages += 1
        full_text += text

    total_chars = len(full_text)
    total_pages = len(reader.pages)

    return {
        "Filename": path.name,
        "Pages": total_pages,
        "Total Chars": total_chars,
        "Empty Pages": empty_pages,
        "SK Chars": sum(1 for c in full_text.lower() if c in SLOVAK_ALPHABET),
        "Density": total_chars / total_pages if total_pages > 0 else 0,
    }


def get_quality_insights(row: pd.Series) -> str:
    issues = []

    if row['Density'] < 500:
        issues.append(f"⚠️ LOW DENSITY ({row['Density']:.0f} chars/pg)")
    elif row['Density'] > 4500:
        issues.append(f"🐘 HIGH DENSITY ({row['Density']:.0f} chars/pg)")


    is_sk = any(kw in row['Filename'].lower() for kw in ["sk", "mirri"])
    if is_sk:
        sk_ratio = (row['SK Chars'] / row['Total Chars']) * 100 if row['Total Chars'] > 0 else 0
        if sk_ratio < 0.5:
            issues.append(f"⚠️ LANGUAGE: Low Slovak ratio ({sk_ratio:.2f}%)")
        else:
            issues.append(f"✅ SLOVAK: Healthy ({sk_ratio:.2f}%)")

    if row['Empty Pages'] > 0:
        issues.append(f"🚩 {row['Empty Pages']} EMPTY PAGES")

    return " | ".join(issues) if issues else "✅ Quality Optimal"


def perform_eda():
    """Main execution flow for the Legal EDA."""

    if not RAW_DATA_DIR.exists():
        print(f"❌ Error: Path {RAW_DATA_DIR} not found.")
        return

    print(f"🧐 Analyzing legal documents in: {RAW_DATA_DIR}")

    results = []
    for file in os.listdir(RAW_DATA_DIR):
        if file.endswith(".pdf"):
            try:
                results.append(analyze_single_pdf(RAW_DATA_DIR / file))
            except Exception as e:
                print(f"⚠️ Skipping {file}: {e}")

    if not results:
        print("No PDF files found to analyze.")
        return

    df = pd.DataFrame(results)

    print("\n" + "=" * 80)
    print(f"{'⚖️  LEXGUARD LEGAL DATA HEALTH REPORT':^80}")
    print("=" * 80)
    print(df.drop(columns=['Density']).to_string(index=False))

    print("\n🔍 PRO-LEVEL DATA QUALITY INSIGHTS")
    print("-" * 40)
    for _, row in df.iterrows():
        insight = get_quality_insights(row)
        print(f"📄 {row['Filename']:.<35} {insight}")


if __name__ == "__main__":
    perform_eda()