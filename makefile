run-prod:
	source ./.env && python3 main.py

install:
	python3 -m pip install -r requirements.txt