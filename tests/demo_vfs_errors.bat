@echo off
cd /d "%~dp0.."
python src\emulator.py --vfs tests\data\broken.json
python src\emulator.py --vfs tests\data\bad_base64.json
python src\emulator.py --vfs tests\data\no_such.json