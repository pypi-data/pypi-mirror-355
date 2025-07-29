# Quality assurance commands
format:
	poetry run black src/ tests/

format-check:
	poetry run black --check --diff src/ tests/

lint:
	poetry run ruff check src/ tests/

lint-fix:
	poetry run ruff check --fix src/ tests/

typecheck:
	poetry run mypy src/ --strict --no-warn-no-return

security:
	poetry run bandit -r src/ -f txt -c .bandit

# Combined quality commands
quality-fix: format lint-fix
	@echo "✅ Auto-fixes completed!"

quality: format-check lint typecheck security test
	@echo "✅ All quality checks passed!"

# Testing commands
test:
	poetry run pytest -n 2 --timeout=120 --cov=src --cov-report=term-missing --cov-report=xml:coverage_reports/coverage.xml --cov-fail-under=85

test-no-cov:
	poetry run pytest

test-cov:
	poetry run pytest -n 2 --timeout=120 --cov=src --cov-report=term-missing --cov-fail-under=85

test-fast:
	poetry run pytest -x

test-serial:
	poetry run pytest --cov=src --cov-report=term-missing --cov-report=xml:coverage_reports/coverage.xml --cov-fail-under=85

coverage-html:
	mkdir -p coverage_reports
	poetry run pytest -n 2 --timeout=120 --cov=src --cov-report=html:coverage_reports/html --cov-fail-under=85
	open coverage_reports/html/index.html

# Development workflow
dev-setup:
	poetry install --with dev

clean:
	rm -rf dist/ build/ *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Build commands
build: clean
	poetry build

.PHONY: format format-check lint lint-fix typecheck security quality quality-fix test test-cov test-fast coverage-html dev-setup clean build 