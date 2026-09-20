@echo off
echo Starting NOVA AI Backend...
call .venv\Scripts\activate.bat
set PYTHONPATH=..
python main.py
