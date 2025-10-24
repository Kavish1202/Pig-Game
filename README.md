# Pig Game

A Pig Game implementation in Python, developed using Object-Oriented Programming principles with comprehensive unit testing.

## Running Tests and Coverage Report

This section provides instructions for running the test suite and generating a test coverage report for the Pig Game project on Windows.

### Prerequisites

- Python 3.8 or higher installed.
- A virtual environment (recommended) with project dependencies installed. To set up:

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
pip install pytest pytest-cov
```

### Running the Test Suite

To execute the full test suite:

```bash
pytest tests
```

### Generating the Coverage Report

To run tests with coverage and generate an HTML report:

```bash
python -m pytest --cov=src tests/ --cov-report=html
```

### Viewing the Coverage Report

To open the coverage report in your default browser:

```bash
Invoke-Item htmlcov/index.html
```