.PHONY: help clean lint build test install release-patch release-minor release-major check

help:
	@echo "Available commands:"
	@echo "  make clean         - Remove build artifacts"
	@echo "  make lint          - Run linting checks"
	@echo "  make build         - Build the package"
	@echo "  make test          - Run tests (if any)"
	@echo "  make install       - Install locally for testing"
	@echo "  make check         - Run all checks (lint)"
	@echo "  make release-patch - Release a patch version (x.x.N+1)"
	@echo "  make release-minor - Release a minor version (x.N+1.0)"
	@echo "  make release-major - Release a major version (N+1.0.0)"

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:
	ruff check src/aluna/

build: clean
	uv build

test:
	@echo "No tests configured yet"

install: build
	uv pip install -e .

check: lint

release-patch:
	./release.sh patch

release-minor:
	./release.sh minor

release-major:
	./release.sh major