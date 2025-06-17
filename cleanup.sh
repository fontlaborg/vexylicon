#!/usr/bin/env bash

# Notice before redirecting output
echo "Starting cleanup process... All output will be logged to cleanup.log"

# Redirect all subsequent output to cleanup.txt
exec >cleanup.txt 2>&1

echo "=== Cleanup started at $(date) ==="

# Check if uv is available, install if not
if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found, installing with pip..."
    python -m pip install uv
fi

echo "python -m uv sync --all-extras"
python -m uv sync --all-extras
echo "python -m uv run hatch clean"
python -m uv run hatch clean
echo "python -m uv run hatch build"
python -m uv run hatch build
echo "python -m uzpy run -e src"
python -m uzpy run -e src

echo "find . -name *.py -exec python -m uv run autoflake -i {} +"
for p in src tests; do find "$p" -name "*.py" -exec python -m uv run autoflake -i {} +; done
echo "find . -name *.py -exec python -m uv run pyupgrade --py311-plus {} +"
for p in src tests; do find "$p" -name "*.py" -exec python -m uv run pyupgrade --py311-plus {} +; done
echo "find . -name *.py -exec python -m uv run ruff check --output-format=github --fix --unsafe-fixes {} +"
for p in src tests; do find "$p" -name "*.py" -exec python -m uv run ruff check --output-format=github --fix --unsafe-fixes {} +; done
echo "find . -name *.py -exec python -m uv run ruff format --respect-gitignore --target-version py311 {} +"
for p in src tests; do find "$p" -name "*.py" -exec python -m uv run ruff format --respect-gitignore --target-version py311 {} +; done
echo "python -m uv run ty check"
python -m uv run ty check
echo "python -m uv run mypy --config-file pyproject.toml src/imgcolorshine tests"
python -m uv run mypy --config-file pyproject.toml src/imgcolorshine tests
if command -v npx >/dev/null 2>&1; then
    echo "npx repomix -i varia,.specstory,AGENT.md,CLAUDE.md,PLAN.md,SPEC.md,llms.txt,.cursorrules,docs -o llms.txt ."
    npx repomix -i varia,.specstory,AGENT.md,CLAUDE.md,PLAN.md,SPEC.md,llms.txt,.cursorrules,docs,.log -o llms.txt .
else
    echo "npx not found, skipping repomix"
fi
echo "python -m uv run hatch test"
python -m uv run hatch test

echo "=== Cleanup completed at $(date) ==="

python ./testdata/example.py
fd -e svg -x svg2png-adam.sh {} 1200
