run:
	python3 src/emulator.py

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v