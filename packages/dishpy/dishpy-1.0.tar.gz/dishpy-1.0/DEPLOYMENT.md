# PyPI Deployment Guide for DishPy

This guide will help you publish DishPy to PyPI so users can install it with `pip install dishpy`.

## Prerequisites

1. **PyPI Account**: Create accounts on:
   - [TestPyPI](https://test.pypi.org/account/register/) (for testing)
   - [PyPI](https://pypi.org/account/register/) (for production)

2. **API Tokens**: Generate API tokens for authentication:
   - Go to Account Settings → API tokens
   - Create a token with "Entire account" scope
   - Save the token securely (you won't see it again)

## Setup Authentication

Configure your API tokens for twine:

```bash
# For TestPyPI (testing)
uv run twine configure --repository testpypi

# For PyPI (production)  
uv run twine configure --repository pypi
```

Or create a `~/.pypirc` file:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-api-token-here
```

## Deployment Steps

### 1. Test Locally

```bash
# Install in development mode
uv pip install -e .

# Test the CLI
dishpy --help
dishpy init
```

### 2. Update Version

Update the version in `pyproject.toml` and `__init__.py`:

```toml
# pyproject.toml
version = "0.1.1"  # increment as needed
```

```python
# __init__.py
__version__ = "0.1.1"
```

### 3. Build Package

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build new distribution
uv run python -m build
```

### 4. Check Package

```bash
# Verify package integrity
uv run twine check dist/*
```

### 5. Test on TestPyPI (Recommended)

```bash
# Upload to TestPyPI first
uv run twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ dishpy
```

### 6. Upload to PyPI

```bash
# Upload to production PyPI
uv run twine upload dist/*
```

### 7. Verify Installation

```bash
# Install from PyPI
pip install dishpy

# Test installation
dishpy --help
```

## Automation Script

Create a deployment script (`deploy.sh`):

```bash
#!/bin/bash
set -e

echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info

echo "🔨 Building package..."
uv run python -m build

echo "✅ Checking package..."
uv run twine check dist/*

echo "🚀 Choose deployment target:"
echo "1) TestPyPI (testing)"
echo "2) PyPI (production)"
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo "📦 Uploading to TestPyPI..."
        uv run twine upload --repository testpypi dist/*
        echo "✨ Test with: pip install --index-url https://test.pypi.org/simple/ dishpy"
        ;;
    2)
        echo "📦 Uploading to PyPI..."
        uv run twine upload dist/*
        echo "✨ Package available at: https://pypi.org/project/dishpy/"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac
```

Make it executable:
```bash
chmod +x deploy.sh
```

## Post-Deployment

1. **Create GitHub Release**: Tag the version and create a release on GitHub
2. **Update Documentation**: Update installation instructions in README
3. **Announce**: Share on relevant communities and social media

## Troubleshooting

### Common Issues

1. **403 Forbidden**: Check your API token and repository configuration
2. **Package already exists**: Increment the version number
3. **Invalid metadata**: Run `twine check dist/*` to identify issues
4. **Binary files too large**: Consider reducing vexcom binary sizes if needed

### Package Size

The current package is ~6.6MB due to vexcom binaries. This is acceptable for PyPI but consider:
- Only including binaries for supported platforms
- Using conditional dependencies for platform-specific binaries
- Documenting the package size in README

## Security Notes

- Never commit API tokens to version control
- Use environment variables or secure credential storage
- Rotate API tokens periodically
- Use scoped tokens when possible (project-specific rather than account-wide)

## Next Steps

After successful deployment:
1. Users can install with: `pip install dishpy`
2. Consider setting up CI/CD for automated deployments
3. Monitor package statistics on PyPI
4. Respond to user issues and feedback