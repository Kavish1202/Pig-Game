# # ===== Setup =====
# venv:
# 	python -m venv .venv

# install:
# 	.venv\\Scripts\\python -m pip install --upgrade pip
# 	@if exist requirements.txt (.venv\\Scripts\\python -m pip install -r requirements.txt)

# init: venv install

# # ===== Testing =====
# test:
# # 	pip install -r requirements.txt
# # 	pip install pytest pytest-cov
# # 	pytest tests/
# 	.venv\\Scripts\\python -m pytest -q
# # ===== Coverage =====

# coverage:
# 	python -m pytest --cov=src tests/ --cov-report=html
# 	powershell -Command "Invoke-Item htmlcov\index.html"
# # ===== Lint & Format =====
# lint:
# 	.venv\\Scripts\\python -m flake8 src
# 	.venv\\Scripts\\python -m pylint src

# format:
# 	.venv\\Scripts\\python -m black src tests

# # ===== Docs (API from docstrings) =====
# doc:
# 	pip install sphinx
# 	python -m sphinx -b html doc\source doc\api
# 	powershell -Command "Invoke-Item doc\api\index.html"
	

# # ===== UML Diagrams =====
# uml:
# 	pyreverse -o png -p pig-game src/pig
# 	move classes_pig-game.png doc\uml\class_diagram.png
# 	move packages_pig-game.png doc\uml\package_diagram.png
# 	powershell -Command "Invoke-Item doc\uml\class_diagram.png"
# 	powershell -Command "Invoke-Item doc\uml\package_diagram.png"


# # ===== Cleanup =====
# clean:
# 	powershell -Command "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue __pycache__, .pytest_cache, htmlcov, .coverage, doc\\api, doc\\uml"

# .PHONY: venv install init test coverage lint format doc uml clean


# ===== Vars =====
PY := .venv\Scripts\python
PIP := .venv\Scripts\pip
VENV_PY := .venv\Scripts\python.exe

# ===== Setup =====
venv:
	@if not exist .venv ( \
		python -m venv .venv \
	)

install: venv
	$(PY) -m pip install --upgrade pip
	@if exist requirements.txt ($(PY) -m pip install -r requirements.txt)

init: install

# ===== Testing =====
# Always run tests from the venv and add src to PYTHONPATH so imports work.
test: install
	$(PY) -m pip install -U pytest pytest-cov
	set "PYTHONPATH=src" && $(PY) -m pytest -q tests

# ===== Coverage =====
coverage: install
	$(PY) -m pip install -U pytest pytest-cov
	set "PYTHONPATH=src" && $(PY) -m pytest --cov=src --cov-report=term-missing --cov-report=html tests
	powershell -Command "if (Test-Path htmlcov\index.html) { Invoke-Item htmlcov\index.html }"

# ===== Lint & Format =====
lint: install
	$(PY) -m pip install -U flake8 pylint
	$(PY) -m flake8 src
	$(PY) -m pylint src

format: install
	$(PY) -m pip install -U black
	$(PY) -m black src tests

# ===== Docs (API from docstrings) =====
doc: install
	$(PY) -m pip install -U sphinx
	$(PY) -m sphinx -b html doc\source doc\api
	powershell -Command "if (Test-Path doc\api\index.html) { Invoke-Item doc\api\index.html }"

# ===== UML Diagrams =====
uml: install
	$(PY) -m pip install -U pylint
	$(PY) -m pylint.pyreverse.main -o png -p pig-game src/pig
	@if exist classes_pig-game.png ( move /Y classes_pig-game.png doc\uml\class_diagram.png )
	@if exist packages_pig-game.png ( move /Y packages_pig-game.png doc\uml\package_diagram.png )
	powershell -Command "if (Test-Path doc\uml\class_diagram.png) { Invoke-Item doc\uml\class_diagram.png }"
	powershell -Command "if (Test-Path doc\uml\package_diagram.png) { Invoke-Item doc\uml\package_diagram.png }"


# ===== Cleanup =====
clean:
	powershell -Command "Remove-Item -Recurse -Force -ErrorAction SilentlyContinue __pycache__, .pytest_cache, htmlcov, .coverage, doc\api, doc\uml"

.PHONY: venv install init test coverage lint format doc uml clean
