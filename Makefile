.PHONY: help install install-dev setup run test coverage lint format type-check security clean docker-build docker-run pre-commit docs

help:
	@echo "🎵 Spotify Playlist Creator - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install          - Install production dependencies"
	@echo "  make install-dev      - Install development dependencies"
	@echo "  make setup            - Complete setup (venv + install + hooks)"
	@echo ""
	@echo "Running:"
	@echo "  make run              - Run the CLI"
	@echo "  make run-brazil       - Create Brazil top 500 playlist"
	@echo "  make run-global       - Create global top 500 playlist"
	@echo "  make preview          - Preview Brazil charts"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run tests"
	@echo "  make test-verbose     - Run tests with verbose output"
	@echo "  make coverage         - Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             - Run all linters"
	@echo "  make format           - Format code with black and isort"
	@echo "  make type-check       - Run mypy type checking"
	@echo "  make security         - Run security scans"
	@echo "  make pre-commit       - Run all pre-commit hooks"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     - Build Docker image"
	@echo "  make docker-run       - Run in Docker container"
	@echo "  make docker-clean     - Clean Docker resources"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean            - Clean up cache and build files"
	@echo "  make clean-all        - Deep clean (including venv)"
	@echo "  make docs             - Generate documentation"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

setup:
	@echo "🔧 Setting up development environment..."
	python -m venv venv
	@echo "✓ Virtual environment created"
	@echo "Run: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"
	@echo "Then run: make install-dev"

run:
	spotichart --help

run-brazil:
	spotichart create --region brazil --limit 500

run-global:
	spotichart create --region global --limit 500

preview:
	spotichart preview --region brazil --limit 20

test:
	pytest tests/ -v

test-verbose:
	pytest tests/ -vv -s

coverage:
	pytest tests/ --cov=spotichart --cov-report=html --cov-report=term
	@echo "📊 Coverage report generated in htmlcov/index.html"

lint:
	@echo "🔍 Running flake8..."
	flake8 src/ --max-line-length=100 --statistics
	@echo "🔍 Running pylint..."
	pylint src/spotichart --fail-under=8.0

format:
	@echo "🎨 Formatting code..."
	black src/ tests/
	isort src/ tests/
	@echo "✓ Code formatted"

type-check:
	@echo "🔍 Type checking with mypy..."
	mypy src/ --ignore-missing-imports

security:
	@echo "🔒 Running security scans..."
	bandit -r src/ -f json -o bandit-report.json
	@echo "✓ Bandit report generated: bandit-report.json"
	safety check --json
	@echo "✓ Safety check complete"

pre-commit:
	pre-commit run --all-files

docker-build:
	@echo "🐳 Building Docker image..."
	docker-compose build
	@echo "✓ Docker image built"

docker-run:
	docker-compose run --rm spotichart config

docker-clean:
	@echo "🧹 Cleaning Docker resources..."
	docker-compose down -v
	docker system prune -f
	@echo "✓ Docker resources cleaned"

clean:
	@echo "🧹 Cleaning cache and build files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/ dist/ build/
	rm -rf logs/*.log
	@echo "✓ Cleanup complete"

clean-all: clean
	@echo "🧹 Deep cleaning..."
	rm -rf venv/
	rm -rf .cache/
	@echo "✓ Deep cleanup complete"

docs:
	@echo "📚 Generating documentation..."
	@echo "Documentation available in docs/ directory"
	@echo "  - ARCHITECTURE.md: Architecture overview"
	@echo "  - README.md: User guide"
	@echo "  - CONTRIBUTING.md: Contribution guidelines"

# Development workflow
.PHONY: dev
dev: install-dev
	@echo "🚀 Development environment ready!"
	@echo "Run 'make run' to start the CLI"

# Release workflow
.PHONY: release
release: clean lint type-check test
	@echo "✓ All checks passed - ready for release!"
