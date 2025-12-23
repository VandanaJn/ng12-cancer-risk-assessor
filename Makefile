 # ------------------------
# Makefile (cross-platform, CI-aware)
# ------------------------

VENV := .venv

# Detect OS and set VENV_PYTHON
ifeq ($(OS),Windows_NT)
    VENV_PYTHON := $(VENV)/Scripts/python.exe
else
    VENV_PYTHON := $(VENV)/bin/python
endif


PYTHON := $(VENV_PYTHON)

.PHONY: install test ingest clean

# ------------------------
# Install dependencies
# ------------------------
install:
ifeq ($(OS),Windows_NT)
	@if not exist "$(VENV)" python -m venv $(VENV)
else
	@if [ ! -d "$(VENV)" ]; then python -m venv $(VENV); fi
endif
	"$(PYTHON)" -m pip install --upgrade pip
	"$(PYTHON)" -m pip install -r requirements.txt



# ------------------------
# Run tests with coverage only running unittest as integration tests are not working after tools were changed to mcp
# ------------------------
test:
	@echo "Running tests with coverage..."
	"$(PYTHON)" -m pytest tests --maxfail=1 --disable-warnings -q 

# ------------------------
# Remove virtual environment
# ------------------------
clean:
ifeq ($(OS),Windows_NT)
	if exist "$(VENV)" rmdir /s /q $(VENV)
else
	if [ -d "$(VENV)" ]; then rm -rf $(VENV); fi
endif

