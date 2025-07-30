init:
	pip install -r requirements.txt
install:
	pip install -e .
test:
	PYTHONPATH=src python -m unittest discover
build:
	python3 -m build
upload:
	python3 -m twine upload dist/*
clean:
	rm -r dist