# Smart Invoice AI

**Private, local AI bookkeeping for freelancers.** Upload a photo of an invoice or receipt, and a local AI reads it and builds your monthly income, expense and profit report. Nothing leaves your computer.

Built for freelancers in Pakistan (PKR support, FBR tax-season report planned), useful for anyone who wants invoice tracking without sending client data to the cloud.

## Features
- **OCR** with RapidOCR reads text from invoice and receipt images (PNG/JPG)
- **Local AI** (via Ollama) extracts date, vendor, total, currency and items as structured JSON
- **Review before saving**: every field is editable, so AI mistakes never reach your books
- **Category suggestions** from keyword rules (Platform Fees, Internet & Utilities, Equipment, ...)
- **Monthly report**: income, expenses, profit, spending by category, CSV export
- **100% local**: SQLite database, no accounts, no cloud

## How it works
```
Image -> RapidOCR (text) -> local LLM via Ollama (JSON) -> editable form -> SQLite -> monthly report
```

## Requirements
- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- About 4 GB of free RAM (works on modest laptops with a small model)

## Installation
```bash
git clone https://github.com/YOUR_USERNAME/smart-invoice-ai.git
cd smart-invoice-ai
pip install -r requirements.txt
ollama pull qwen2.5:3b
```

## Usage
```bash
python -m streamlit run invoice_app.py
```
On Windows you can also double-click `run_app.bat`. The app opens at `http://localhost:8501`.

1. **Add invoice**: upload an image, check the extracted fields, fix anything wrong, press Save.
2. **Transactions**: see and delete saved entries.
3. **Monthly report**: income, expenses, profit and a category breakdown.

## Choosing the AI model
The default model is `qwen2.5:3b`. Use another Ollama model with the `SMART_INVOICE_MODEL` environment variable:

```powershell
# Windows PowerShell
$env:SMART_INVOICE_MODEL = "qwen2.5:7b"
python -m streamlit run invoice_app.py
```

Larger models read invoices more accurately but need more RAM.

> **Licensing note:** `qwen2.5:3b` is released under the Qwen Research License (non-commercial). If you plan to use or sell this app commercially, use a model with a commercial-friendly license, such as `qwen2.5:1.5b` or `qwen2.5:7b` (Apache 2.0), and check the license of whichever model you choose.

## Project structure
| File | Purpose |
|---|---|
| `invoice_app.py` | Streamlit user interface |
| `extractor.py` | OCR and local AI extraction |
| `ledger.py` | SQLite storage and monthly summaries |
| `run_app.bat` | One-click launcher for Windows |
| `requirements.txt` | Python dependencies |

## Privacy
Invoices, the database and the AI model all stay on your machine. The `data/` folder (uploaded images and `ledger.db`) is excluded from Git on purpose. Never commit real invoices.

## Known limitations
- Small models can confuse the issuer and the customer on complex invoices, so always review the vendor field.
- OCR accuracy drops on blurry or very small text.
- Currency is only detected when a code (USD, PKR, ...) is written on the invoice; otherwise your default currency is used.

## Roadmap
- [ ] PDF export
- [ ] FBR tax-season report
- [ ] Urdu invoice support
- [ ] Windows installer

## License
Copyright (c) 2026 [YOUR NAME]. All rights reserved. See [LICENSE](LICENSE). Third-party components are covered by their own licenses.
