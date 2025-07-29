# 🚀 py-pglite Development Commands
# ================================
#
# Vite-style convenience commands for development
# Supports pip, PDM, and UV package managers

.PHONY: help dev test examples lint quick clean install

# Default target
help:
	@echo "🚀 py-pglite Development Commands"
	@echo "================================"
	@echo ""
	@echo "Core Commands:"
	@echo "  make dev         Run full development workflow (like CI)"
	@echo "  make test        Run tests only"
	@echo "  make examples    Run examples only"
	@echo "  make lint        Run linting only"
	@echo "  make quick       Quick checks for development"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make install     Install in development mode"
	@echo "  make clean       Clean build artifacts"
	@echo "  make fmt         Auto-fix formatting"
	@echo ""
	@echo "Package Manager Support:"
	@echo "  make dev         # Standard pip commands"
	@echo "  PDM_RUN_CWD=. make dev    # Use PDM"
	@echo "  UV=1 make dev            # Use UV"
	@echo ""
	@echo "Example Usage:"
	@echo "  make dev         # Full workflow (linting + tests + examples)"
	@echo "  make quick       # Quick checks during development"
	@echo "  make test        # Just run the test suite"

# Full development workflow (mirrors CI exactly)
dev:
	@echo "🚀 Running full development workflow..."
	python scripts/dev.py

# Run tests only
test:
	@echo "🧪 Running test suite..."
	python scripts/dev.py --test

# Run examples only
examples:
	@echo "📚 Running examples..."
	python scripts/dev.py --examples

# Run linting only
lint:
	@echo "🎨 Running linting checks..."
	python scripts/dev.py --lint

# Quick checks for development
quick:
	@echo "⚡ Running quick development checks..."
	python scripts/dev.py --quick

# Install in development mode
install:
	@echo "📦 Installing in development mode..."
	pip install -e ".[dev]"
	pip install types-psutil

# Auto-fix formatting
fmt:
	@echo "🎨 Auto-fixing formatting..."
	ruff format py_pglite/
	@echo "✅ Formatting complete!"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleanup complete!"

# Show project status
status:
	@echo "📊 Project Status"
	@echo "================"
	@echo "Python version: $(shell python --version)"
	@echo "Pip packages:"
	@pip list | grep -E "(ruff|mypy|pytest|pglite)" || echo "Development packages not installed"
	@echo ""
	@echo "Quick test:"
	@python -c "import py_pglite; print(f'py-pglite {py_pglite.__version__} ready!')" 2>/dev/null || echo "py-pglite not installed in dev mode" 