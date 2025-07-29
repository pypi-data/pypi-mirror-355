# Evolve Development Makefile
# Common commands to avoid CI failures and speed up development

.PHONY: help install test format lint check clean docs e2e

help:  ## Show this help message
	@echo "Evolve Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install all dependencies and tools
	uv sync --all-extras
	uv tool install aider-chat
	uv tool install pre-commit --with pre-commit-uv
	pre-commit install

test:  ## Run all tests
	uv run pytest -v

test-fast:  ## Run tests without slow integration tests
	uv run pytest -v -m "not slow"

test-cov:  ## Run tests with coverage report
	uv run pytest -v --cov=src/evolve --cov-report=term-missing

format:  ## Format code (run before committing!)
	uv run ruff format .
	uv run ruff check . --fix

lint:  ## Check code style without fixing
	uv run ruff check .
	uv run ruff format --check .

check:  ## Run all checks (format, lint, tests)
	@$(MAKE) format
	@$(MAKE) lint
	@$(MAKE) test

clean:  ## Clean up temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache
	rm -rf .ruff_cache

docs:  ## Generate documentation
	@echo "Checking documentation structure..."
	@ls -la docs/
	@echo ""
	@echo "Available documentation:"
	@echo "  - docs/adr/             Architecture Decision Records"
	@echo "  - docs/development-patterns.md"
	@echo "  - docs/error-log.md"
	@echo "  - docs/codebase-map.md"

e2e:  ## Run end-to-end tests (requires API keys)
	./scripts/test_e2e.py --scenario simple --verbose

e2e-all:  ## Run all end-to-end tests
	./scripts/test_e2e.py --scenario all --iterations 3

pr-ready:  ## Ensure code is ready for PR (run all checks)
	@echo "🔍 Running pre-PR checks..."
	@$(MAKE) format
	@echo "✅ Formatting complete"
	@$(MAKE) lint
	@echo "✅ Linting passed"
	@$(MAKE) test
	@echo "✅ Tests passed"
	@echo ""
	@echo "🎉 Code is ready for PR!"
	@echo "Remember to:"
	@echo "  1. Update docs if needed"
	@echo "  2. Add ADR for significant decisions"
	@echo "  3. Update error-log.md if you encountered issues"
