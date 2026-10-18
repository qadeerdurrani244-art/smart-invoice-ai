@echo off
cd /d "%~dp0"
echo Starting Smart Invoice AI... (Ollama should be running)
python -m streamlit run invoice_app.py
pause
