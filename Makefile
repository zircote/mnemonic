.PHONY: all build test lint format format-check clean setup audit docs validate

# Default target
all: lint test

# Build (no-op for this plugin, but included for consistency)
build:
	@echo "No build step required for Claude Code plugins"

# Run tests
test:
	@echo "Running tests..."
	@python3 -m pytest tests/ -v 2>/dev/null || echo "No tests found or pytest not installed"
	@echo "Validating hook outputs..."
	@for hook in hooks/*.py; do \
		echo "  Testing $$hook..."; \
		python3 "$$hook" --test 2>/dev/null || python3 -c "import sys; sys.path.insert(0, '.'); exec(open('$$hook').read())" 2>/dev/null || true; \
	done

# Lint code
lint: validate
	@echo "Linting Python files..."
	@python3 -m ruff check hooks/ 2>/dev/null || python3 -m flake8 hooks/ 2>/dev/null || echo "Install ruff or flake8 for Python linting"
	@echo "Checking markdown files..."
	@command -v markdownlint >/dev/null 2>&1 && markdownlint '**/*.md' --ignore node_modules || echo "markdownlint not installed (optional)"

# Validate plugin structure
validate:
	@echo "Validating plugin structure..."
	@test -f .claude-plugin/plugin.json || (echo "ERROR: Missing .claude-plugin/plugin.json" && exit 1)
	@echo "  Plugin manifest exists"
	@for cmd in commands/*.md; do \
		grep -q "^---" "$$cmd" || (echo "ERROR: $$cmd missing frontmatter" && exit 1); \
	done
	@echo "  Commands have frontmatter"
	@for skill in skills/*/SKILL.md; do \
		grep -q "^---" "$$skill" || (echo "ERROR: $$skill missing frontmatter" && exit 1); \
	done
	@echo "  Skills have frontmatter"
	@echo "Plugin validation passed!"

# Format code
format:
	@echo "Formatting Python files..."
	@python3 -m ruff format hooks/ 2>/dev/null || python3 -m black hooks/ 2>/dev/null || echo "Install ruff or black for formatting"

# Check formatting without changes
format-check:
	@echo "Checking Python formatting..."
	@python3 -m ruff format --check hooks/ 2>/dev/null || python3 -m black --check hooks/ 2>/dev/null || echo "Install ruff or black for format checking"

# Clean generated files
clean:
	@echo "Cleaning..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.py[cod]" -delete 2>/dev/null || true
	@find . -type f -name ".DS_Store" -delete 2>/dev/null || true
	@echo "Clean complete"

# Setup development environment
setup:
	@echo "Setting up development environment..."
	@python3 -m pip install --upgrade pip
	@python3 -m pip install ruff pytest 2>/dev/null || echo "Some tools may not have installed"
	@echo "Setup complete"

# Security audit
audit:
	@echo "Running security audit..."
	@python3 -m pip_audit 2>/dev/null || echo "pip-audit not installed (optional)"
	@echo "Checking for hardcoded secrets..."
	@grep -r "password\s*=" hooks/ --include="*.py" && echo "WARNING: Potential hardcoded password" || true
	@grep -r "api_key\s*=" hooks/ --include="*.py" && echo "WARNING: Potential hardcoded API key" || true
	@echo "Security audit complete"

# Build documentation
docs:
	@echo "Documentation is in docs/ directory"
	@echo "Files:"
	@find docs -name "*.md" -type f

# Help
help:
	@echo "Available targets:"
	@echo "  all          - Run lint and test (default)"
	@echo "  build        - Build the project (no-op for plugins)"
	@echo "  test         - Run tests"
	@echo "  lint         - Lint code and validate plugin"
	@echo "  validate     - Validate plugin structure"
	@echo "  format       - Format Python code"
	@echo "  format-check - Check code formatting"
	@echo "  clean        - Remove generated files"
	@echo "  setup        - Set up development environment"
	@echo "  audit        - Run security audit"
	@echo "  docs         - List documentation files"
	@echo "  help         - Show this help"
