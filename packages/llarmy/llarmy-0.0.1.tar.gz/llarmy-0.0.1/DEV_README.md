# llarmy

A plethora of llama-index based agents and tools to create agentic systems

## Development Setup

### Quick Start

1. **Activate the development environment:**
   ```bash
   # Windows
   activate_dev.bat
   
   # Linux/macOS  
   source venv/bin/activate
   export PYTHONPATH=$PWD/src:$PYTHONPATH
   ```

2. **Install development dependencies:**
   ```bash
   python scripts/setup_dev.py
   ```

### Development Commands

- **Setup:** `python scripts/setup_dev.py` - Install all dev dependencies
- **Lint:** `python scripts/lint.py` - Run all linting (ruff, mypy, pylint)
- **Format:** `python scripts/format.py` - Auto-format code with black and ruff
- **Test:** `python scripts/test.py` - Run tests with pytest
- **Build:** `python scripts/build.py` - Build package for distribution

### Project Structure

```
llarmy/
├── src/llarmy/          # Main package code
├── tests/               # Test files  
├── scripts/             # Development scripts
├── venv/                # Virtual environment
├── pyproject.toml       # Package configuration
└── activate_dev.bat     # Windows dev environment activation
```

## Package Upload

1. **Build the package:** `python scripts/build.py`
2. **Check package:** `twine check dist/*`
3. **Upload to TestPyPI:** `twine upload --repository testpypi dist/*`
4. **Upload to PyPI:** `twine upload dist/*`