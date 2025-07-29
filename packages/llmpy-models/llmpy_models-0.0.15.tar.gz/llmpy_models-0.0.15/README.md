# llmpy-models Auto Generator

This project includes a script to regenerate and publish the `llmpy_models.py` file automatically.

## Requirements

To run `scripts/publish.sh`, ensure the following are available:

- **Python** ≥ 3.10
- **Virtual environment** in `.venv/` with dependencies installed
- **macOS** (due to `sed -i ''` syntax)
- **Tools installed**:
  - `twine`
  - `build`
  - `diff`
  - `sed`

Make sure the update.sh script is executable:
`chmod +x scripts/update.sh`
