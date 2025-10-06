# ===== Setup =====
venv:
	python -m venv .venv

install:
	.venv\\Scripts\\python -m pip install --upgrade pip
	@if exist requirements.txt (.venv\\Scripts\\python -m pip install -r requirements.txt)

init: venv install

# ===== Testing =====
test:
	.venv\\Scripts\\python -m pytest -q

coverage:
	.venv\\Scripts\\python -m pytest --cov=src --cov-report=term-missing

# ===== Lint & Format =====
lint:
	.venv\\Scripts\\python -m flake8 src
	.venv\\Scripts\\python -m pylint src

format:
	.venv\\Scripts\\python -m black src tests

# ===== Docs (API from docstrings) =====
doc:
	@if not exist doc\\api mkdir doc\\api
	.venv\\Scripts\\python -m pdoc --html src --output-dir doc/api --force

# ===== UML Diagrams =====
uml:
	@if not exist doc\\uml mkdir doc\\uml
	.venv\\Scripts\\python -m pyreverse src -o png -p PigGame
	@move /Y classes_PigGame.png doc\\uml\\ >NUL 2>&1
	@move /Y packages_PigGame.png doc\\uml\\ >NUL 2>&1

# ===== Cleanup =====
clean:
	powershell -Command "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue __pycache__, .pytest_cache, htmlcov, .coverage, doc\\api, doc\\uml"

.PHONY: venv install init test coverage lint format doc uml clean
