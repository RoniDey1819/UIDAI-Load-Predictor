@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Running Aadhaar Analysis...
python main.py

echo.
pause
