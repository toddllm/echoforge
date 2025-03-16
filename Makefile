# EchoForge Makefile
# Provides commands for development, testing, and deployment

.PHONY: setup test lint format coverage clean pre-commit check docs build deploy run dev dev-debug help

# Default target
.DEFAULT_GOAL := help

PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
BLACK := $(PYTHON) -m black
ISORT := $(PYTHON) -m isort
FLAKE8 := $(PYTHON) -m flake8
MYPY := $(PYTHON) -m mypy
PORT ?= 9001

# Colors for terminal output
BOLD := $(shell tput bold)
NORMAL := $(shell tput sgr0)
GREEN := $(shell tput setaf 2)
YELLOW := $(shell tput setaf 3)
BLUE := $(shell tput setaf 4)
RED := $(shell tput setaf 1)

# Help command
help:
	@echo "$(BOLD)EchoForge Makefile$(NORMAL)"
	@echo "Available commands:"
	@echo "  $(YELLOW)setup$(NORMAL)        Install dependencies and set up development environment"
	@echo "  $(YELLOW)test$(NORMAL)         Run tests"
	@echo "  $(YELLOW)lint$(NORMAL)         Run linting checks"
	@echo "  $(YELLOW)format$(NORMAL)       Format code using black and isort"
	@echo "  $(YELLOW)coverage$(NORMAL)     Run tests with coverage report"
	@echo "  $(YELLOW)clean$(NORMAL)        Clean up build artifacts and cache files"
	@echo "  $(YELLOW)pre-commit$(NORMAL)   Run all pre-commit checks"
	@echo "  $(YELLOW)check$(NORMAL)        Run all tests and checks"
	@echo "  $(YELLOW)docs$(NORMAL)         Generate documentation"
	@echo "  $(YELLOW)build$(NORMAL)        Build package"
	@echo "  $(YELLOW)deploy$(NORMAL)       Deploy application"
	@echo "  $(YELLOW)run$(NORMAL)          Run the application"
	@echo "  $(YELLOW)dev$(NORMAL)          Run the application in development mode"
	@echo "  $(YELLOW)dev-debug$(NORMAL)    Run the application in debug mode"
	@echo ""
	@echo "Usage: make [target]"

# Setup development environment
setup:
	@echo "$(BOLD)Setting up development environment...$(NORMAL)"
	$(PIP) install -e ".[dev]"
	@echo "$(GREEN)Setup complete.$(NORMAL)"

# Run tests
test:
	@echo "$(BOLD)Running tests...$(NORMAL)"
	$(PYTEST) tests/

# Run linting checks
lint:
	@echo "$(BOLD)Running linting checks...$(NORMAL)"
	$(FLAKE8) app/ tests/
	$(ISORT) --check-only app/ tests/
	$(BLACK) --check app/ tests/
	$(MYPY) app/

# Format code using black and isort
format:
	@echo "$(BOLD)Formatting code...$(NORMAL)"
	$(ISORT) app/ tests/
	$(BLACK) app/ tests/
	@echo "$(GREEN)Code formatted.$(NORMAL)"

# Run tests with coverage
coverage:
	@echo "$(BOLD)Running tests with coverage...$(NORMAL)"
	$(PYTEST) --cov=app --cov-report=term-missing --cov-report=html tests/
	@echo "$(GREEN)Coverage report generated.$(NORMAL)"
	@echo "Open htmlcov/index.html to view the report."

# Clean up build artifacts and cache files
clean:
	@echo "$(BOLD)Cleaning up...$(NORMAL)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "$(GREEN)Cleanup complete.$(NORMAL)"

# Run pre-commit checks
pre-commit: format lint test
	@echo "$(GREEN)All pre-commit checks passed.$(NORMAL)"

# Run all tests and checks
check: lint test
	@echo "$(GREEN)All checks passed.$(NORMAL)"

# Generate documentation
docs:
	@echo "$(BOLD)Generating documentation...$(NORMAL)"
	@echo "Documentation generation not yet implemented."

# Build package
build: clean
	@echo "$(BOLD)Building package...$(NORMAL)"
	$(PYTHON) setup.py sdist bdist_wheel
	@echo "$(GREEN)Build complete.$(NORMAL)"

# Deploy application
deploy:
	@echo "$(BOLD)Deploying application...$(NORMAL)"
	@echo "Deployment not yet implemented."

# Run the application
run:
	@echo "$(BOLD)Running application...$(NORMAL)"
	cd $(CURDIR) && $(PYTHON) -m app.main

# Run the application in development mode
dev:
	@echo "$(BOLD)Running application in development mode...$(NORMAL)"
	cd $(CURDIR) && PYTHONPATH=$(CURDIR) uvicorn app.main:app --reload --port $(PORT)

# Run the application in debug mode
dev-debug:
	@echo "$(BOLD)Running application in debug mode...$(NORMAL)"
	cd $(CURDIR) && PYTHONPATH=$(CURDIR) LOG_LEVEL=DEBUG uvicorn app.main:app --reload --port $(PORT) --log-level debug 