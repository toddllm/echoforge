.PHONY: setup test lint build run clean

setup:
	pip install -r requirements-dev.txt

test:
	pytest tests/

lint:
	flake8 app/ tests/
	mypy app/
	black --check app/ tests/
	isort --check app/ tests/

format:
	black app/ tests/
	isort app/ tests/

build:
	docker-compose build

run:
	docker-compose up

clean:
	docker-compose down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete 