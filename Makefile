.PHONY: help install setup run test clean venv init-db

# Default target
help:
	@echo "MediAnalyze Pro - Makefile Commands"
	@echo "===================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make setup      - Create virtual environment and install dependencies"
	@echo "  make install    - Install Python dependencies (requires active venv)"
	@echo "  make run        - Run the GUI application"
	@echo "  make test       - Run all tests"
	@echo "  make test-cov   - Run tests with coverage report"
	@echo "  make init-db    - Initialize database"
	@echo "  make clean      - Remove temporary files and caches"
	@echo "  make venv       - Create virtual environment only"
	@echo ""

# Create virtual environment
venv:
	@echo "Creating virtual environment..."
	python3 -m venv venv
	@echo "Virtual environment created. Activate it with: source venv/bin/activate"

# Full setup: create venv and install dependencies
setup: venv
	@echo "Setting up MediAnalyze Pro..."
	@echo "Activating virtual environment and installing dependencies..."
	@bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
	@echo ""
	@echo "Setup complete! Activate the virtual environment with:"
	@echo "  source venv/bin/activate"
	@echo "Then run the application with: make run"

# Install dependencies (assumes venv is active)
install:
	@echo "Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	@echo "Dependencies installed successfully!"

# Run the GUI application
run:
	@echo "Starting MediAnalyze Pro..."
	python run_gui.py

# Run all tests
test:
	@echo "Running tests..."
	pytest tests/ -v

# Run tests with coverage
test-cov:
	@echo "Running tests with coverage..."
	pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/"

# Initialize database
init-db:
	@echo "Initializing database..."
	python -m src.database.init_db
	@echo "Database initialized successfully!"

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	@echo "Cleanup complete!"

# Clean everything including virtual environment
clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf venv
	@echo "All cleanup complete!"
