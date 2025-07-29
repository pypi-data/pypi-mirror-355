.PHONY: test test-coverage test-watch install install-dev clean

# Install dependencies
install:
	pip install -e .

install-dev:
	pip install -e ".[dev,test]"

# Run tests
test:
	pytest

test-coverage:
	pytest --cov=src/voice_mcp --cov-report=html --cov-report=term

test-watch:
	pytest-watch

# Run specific test file
test-file:
	@test -n "$(FILE)" || (echo "Usage: make test-file FILE=test_voice_mcp.py" && exit 1)
	pytest tests/$(FILE) -v

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info