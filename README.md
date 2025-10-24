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

### Prerequisites for Documentation Generation
In addition to the project dependencies, install Sphinx:

```bash
pip install sphinx
```

### Build documentation:
```bash
python -m sphinx -b html doc\source doc\api
```
### View documentation
```bash
Invoke-Item doc\api\index.html
```

## Generating UML Diagrams

Uses Pyreverse to reverse-engineer code into PNG diagrams in `doc/uml`.

### Prerequisites
```bash
pip install pylint
choco install graphviz
```

### Build Diagrams
```bash
pyreverse -o png -p pig-game src/pig
move classes_pig-game.png doc\uml\class_diagram.png
move packages_pig-game.png doc\uml\package_diagram.png
```
### View Diagrams

```bash
Invoke-Item doc\uml\class_diagram.png
Invoke-Item doc\uml\package_diagram.png
```