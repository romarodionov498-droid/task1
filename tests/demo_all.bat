@echo off
cd /d "%~dp0.."
python src\emulator.py --vfs tests\data\files.json --script tests\scripts\errors.txt