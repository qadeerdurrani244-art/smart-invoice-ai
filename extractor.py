"""
extractor.py
Invoice/receipt image -> OCR text -> qwen2.5:3b -> JSON

Test karne ke liye:
    python extractor.py "C:\\Users\\PMLS\\Desktop\\test.png"
"""
import json
import os
import sys

import ollama
from rapidocr_onnxruntime import RapidOCR

MODEL = os.environ.get("SMART_INVOICE_MODEL", "qwen2.5:3b")
_ocr = None  # OCR ek hi baar load hoga (tez rehta hai)

PROMPT = """You are an invoice/receipt data extractor.
Below is OCR text from an invoice or receipt. It may contain small spelling mistakes.
Return ONLY a JSON object with exactly these keys:
{
  "date": "YYYY-MM-DD or null",
  "vendor": "business or client name or null",
  "total": number or null,
  "currency": "PKR, USD, EUR, etc. or null",
  "type": "income or expense",
  "items": ["short item descriptions"]
}
Rules:
- total must be a plain number (no commas, no currency symbol).
- If a value is not clearly in the text, use null. Do NOT guess.
- vendor is the business that ISSUED the invoice (the company in the header/logo, or the one that says "Thank you for choosing ..."). It is NOT the customer (the one under "Bill To", "Customer" or "Client").
- currency: only fill it if a currency code (USD, PKR, AUD, EUR...) or words like Rs/Rupees are written. A lone "$" sign is NOT enough, use null.
- type is "income" if this is an invoice the user sent to a client, "expense" if it is a bill/receipt the user paid.

OCR TEXT:
"""


def ocr_text(image_path):
    """Image se text nikalta hai."""
    global _ocr
    if _ocr is None:
        _ocr = RapidOCR()
    result, _ = _ocr(image_path)
    if not result:
        return ""
    return "\n".join(line[1] for line in result)


def extract_invoice(image_path, retries=2):
    """Image -> dict (date, vendor, total, currency, type, items, raw_text)."""
    text = ocr_text(image_path)
    if not text.strip():
        return {"error": "Image se koi text nahi mila", "raw_text": ""}

    last_error = None
    for _ in range(retries + 1):
        try:
            response = ollama.chat(
                model=MODEL,
                messages=[{"role": "user", "content": PROMPT + text}],
                format="json",
                options={"temperature": 0},
            )
            data = json.loads(response["message"]["content"])
            data["raw_text"] = text
            return data
        except Exception as e:  # JSON kharab ho ya Ollama error de, dobara try
            last_error = e

    return {"error": str(last_error), "raw_text": text}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Use: python extractor.py "path\\to\\image.png"')
        sys.exit(1)
    out = extract_invoice(sys.argv[1])
    print(json.dumps(out, indent=2, ensure_ascii=False))
