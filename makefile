fmt:
	@echo "Formatting ai-experiments code"
	@poetry run python -m ruff format
	@echo "Formatted chatot code"

fix:
	@echo "Checking ai-experiments code"
	@poetry run python -m ruff check --fix
	@echo "Checked chatot code"

run:
	@echo "Running chatot"
	@poetry run python -d -m chatot.main

update:
	@poetry lock --no-cache
	@poetry install

.PHONY: fmt fix run update
