@echo off
title FastBox Delivery Control Center
if not exist venv (
  echo Creating virtual environment...
  python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
echo.
echo Starting FastBox Web Software...
echo Open http://127.0.0.1:5000 in your browser.
echo Press CTRL+C to stop.
python app.py
pause
