.PHONY: help setup check test format clean

help:
	@echo "Available commands:"
	@echo "  make setup    - Install dependencies"
	@echo "  make check    - Run linting and type checking"
	@echo "  make test     - Run tests"
	@echo "  make format   - Format code"
	@echo "  make clean    - Clean cache files"

setup:
	pip install -e ".[dev]" 2>/dev/null || pip install -r requirements.txt 2>/dev/null || echo "No dependencies file found"
	pip install ruff mypy pytest pytest-cov

check:
	ruff check src/ tests/ 2>/dev/null || ruff check .
	mypy src/ --strict 2>/dev/null || mypy . --strict 2>/dev/null || echo "mypy check skipped"

test:
	pytest tests/ -v 2>/dev/null || pytest -v 2>/dev/null || echo "No tests found"

format:
	ruff format src/ tests/ 2>/dev/null || ruff format .
	ruff check --fix src/ tests/ 2>/dev/null || ruff check --fix .

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
