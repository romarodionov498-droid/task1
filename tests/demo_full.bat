@echo off
cd /d "%~dp0.."
python src\emulator.py --vfs tests\data\deep.json --script tests\scripts\full.txt