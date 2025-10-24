# ===== Setup =====
venv:
	python -m venv .venv

install:
	.venv\\Scripts\\python -m pip install --upgrade pip
	@if exist requirements.txt (.venv\\Scripts\\python -m pip install -r requirements.txt)

init: venv install

# ===== Testing =====
test:
	pip install -r requirements.txt
	pip install pytest pytest-cov
	pytest tests/

# ===== Coverage =====

coverage:
	python -m pytest --cov=src tests/ --cov-report=html
	powershell -Command "Invoke-Item htmlcov\index.html"
# ===== Lint & Format =====
lint:
	.venv\\Scripts\\python -m flake8 src
	.venv\\Scripts\\python -m pylint src

format:
	.venv\\Scripts\\python -m black src tests

# ===== Docs (API from docstrings) =====
doc:
	pip install sphinx
	python -m sphinx -b html doc\source doc\api
	powershell -Command "Invoke-Item doc\api\index.html"
	

# ===== UML Diagrams =====
uml:
	pyreverse -o png -p pig-game src/pig
	move classes_pig-game.png doc\uml\class_diagram.png
	move packages_pig-game.png doc\uml\package_diagram.png
	powershell -Command "Invoke-Item doc\uml\class_diagram.png"
	powershell -Command "Invoke-Item doc\uml\package_diagram.png"


# ===== Cleanup =====
clean:
	powershell -Command "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue __pycache__, .pytest_cache, htmlcov, .coverage, doc\\api, doc\\uml"

.PHONY: venv install init test coverage lint format doc uml clean


