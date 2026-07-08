#!/usr/bin/env bash
# Matsya — Virtual environment setup
# Run: bash setup_venv.sh

set -e
cd "$(dirname "$0")"

VENV_DIR=".venv"

echo "Creating virtual environment in ${VENV_DIR}/..."
python3 -m venv "$VENV_DIR"

echo "Activating and installing dependencies..."
source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install opencode-ai

echo ""
echo "✓ Virtual environment ready."
echo "  Activate with: source ${VENV_DIR}/bin/activate"
echo ""
echo "Matsya's dependencies installed. The opencode SDK is available for agent dispatch."
