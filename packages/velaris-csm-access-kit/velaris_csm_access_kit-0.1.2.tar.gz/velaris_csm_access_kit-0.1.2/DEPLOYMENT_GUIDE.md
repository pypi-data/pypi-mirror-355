# Velaris CSM Access Kit - Deployment Guide

This guide provides all the steps needed to deploy your `velaris-csm-access-kit` library to Git and PyPI using uv.

## 📋 Prerequisites

- [uv](https://docs.astral.sh/uv/) installed on your system
- Git installed and configured
- GitHub account (or other Git hosting service)
- PyPI account for publishing

## 🚀 Step-by-Step Deployment Process

### 1. Package Structure (✅ Already Complete)

Your package is already properly structured:

```
velaris_csm_access_kit/
├── .gitignore
├── .python-version
├── LICENSE
├── README.md
├── pyproject.toml
├── src/
│   └── velaris_csm_access_kit/
│       ├── __init__.py
│       ├── cache.py
│       ├── db.py
│       ├── py.typed
│       ├── secrets.py
│       ├── service_registry.py
│       └── token.py
└── test_import.py
```

### 2. Git Repository Setup (✅ Already Complete)

The Git repository has been initialized and the initial commit has been made:

```bash
cd velaris_csm_access_kit
git status  # Should show clean working directory
```

### 3. Create GitHub Repository

1. Go to [GitHub](https://github.com) and create a new repository
2. Name it: `velaris-csm-access-kit`
3. Don't initialize with README (we already have one)
4. Add the remote origin:

```bash
cd velaris_csm_access_kit
git remote add origin https://github.com/YOUR_USERNAME/velaris-csm-access-kit.git
git branch -M main
git push -u origin main
```

### 4. Build and Test Package (✅ Already Verified)

The package builds successfully and all imports work:

```bash
cd velaris_csm_access_kit
uv build  # Creates dist/ directory with wheel and source distribution
uv run python test_import.py  # Verifies all imports work
```

### 5. Publishing to PyPI

#### Option A: Using uv (Recommended)

1. **Install twine** (if not already installed):
```bash
uv add --dev twine
```

2. **Build the package**:
```bash
uv build
```

3. **Upload to TestPyPI first** (recommended for testing):
```bash
uv run twine upload --repository testpypi dist/*
```

4. **Test installation from TestPyPI**:
```bash
# In a new directory
uv add --index-url https://test.pypi.org/simple/ velaris-csm-access-kit
```

5. **Upload to PyPI** (production):
```bash
uv run twine upload dist/*
```

#### Option B: Using PyPI API Token (Recommended for Security)

1. **Create PyPI API Token**:
   - Go to [PyPI Account Settings](https://pypi.org/manage/account/token/)
   - Create a new API token
   - Copy the full token (including `pypi-` prefix)

2. **Configure credentials using the setup script**:
```bash
python setup_pypi_credentials.py
# Enter your API token when prompted
```

3. **Or manually create ~/.pypirc file**:
```ini
[distutils]
index-servers = 
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_FULL_API_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_FULL_API_TOKEN_HERE
```

4. **Upload**:
```bash
# To TestPyPI first (recommended)
uv run twine upload --repository testpypi dist/*

# To production PyPI
uv run twine upload dist/*
```

#### Troubleshooting Upload Issues

If you get a `403 Forbidden` error:

1. **Check your API token**: Make sure it includes the `pypi-` prefix
2. **Verify .pypirc format**: Use the setup script or check the format above
3. **Check package name**: Ensure the name isn't already taken on PyPI
4. **File permissions**: Ensure `.pypirc` has correct permissions (600)

### 6. Installation Methods

Once published, users can install your package using:

#### Using uv (Recommended):
```bash
uv add velaris-csm-access-kit
```

#### Using pip:
```bash
pip install velaris-csm-access-kit
```

### 7. Version Management

This package uses **automatic versioning** based on Git tags using `hatch-vcs`. The version is automatically determined from your Git tags.

#### Automated Release Process

Use the provided release script for easy version management:

```bash
# Create a new release (creates tag, builds, and optionally publishes)
python scripts/release.py --version 0.1.1 --publish

# Or test with TestPyPI first
python scripts/release.py --version 0.1.1 --test-pypi --publish

# Just create tag and build (no publishing)
python scripts/release.py --version 0.1.1
```

#### Manual Release Process

1. **Create and push a Git tag**:
```bash
git tag v0.1.1
git push origin v0.1.1
```

2. **Build package** (version automatically detected from tag):
```bash
uv build
```

3. **Publish**:
```bash
uv run twine upload dist/*
```

#### Version Format

- Use semantic versioning: `MAJOR.MINOR.PATCH`
- Tags should be prefixed with `v`: `v0.1.1`, `v1.0.0`, etc.
- Development versions are automatically generated between tags

#### How It Works

- **Git tags** determine the official version numbers
- **hatch-vcs** automatically generates version from Git history
- **No manual version updates** needed in code files
- **Development builds** get automatic `.devN` suffixes

### 8. Development Workflow

For ongoing development:

1. **Install development dependencies**:
```bash
uv sync --extra dev
```

2. **Run tests**:
```bash
uv run pytest  # When you add proper tests
```

3. **Format code**:
```bash
uv run black src/
uv run isort src/
```

4. **Type checking**:
```bash
uv run mypy src/
```

## 🔧 Configuration Files

### pyproject.toml
- ✅ Properly configured with dependencies
- ✅ Metadata and classifiers set
- ✅ Build system configured

### README.md
- ✅ Comprehensive documentation
- ✅ Installation instructions
- ✅ Usage examples
- ✅ API reference

### LICENSE
- ✅ MIT License included

## 📦 Package Features

Your library provides:

- **Token Management**: JWT validation and service-based token generation
- **Caching**: TTL-based caching system
- **Database Connection Pooling**: Async PostgreSQL with AWS SSM integration
- **Service Registry**: AWS SSM-based service discovery
- **Secrets Management**: AWS Secrets Manager integration

## 🧪 Testing

The package has been tested and verified:
- ✅ All imports work correctly
- ✅ Basic functionality tested
- ✅ Dependencies resolve properly
- ✅ Package builds successfully

## 📚 Next Steps

1. **Create GitHub repository** and push your code
2. **Set up PyPI account** if you don't have one
3. **Publish to TestPyPI** first for testing
4. **Publish to PyPI** for production use
5. **Add CI/CD pipeline** (GitHub Actions) for automated testing and publishing
6. **Write comprehensive tests** using pytest
7. **Set up documentation** (optional: using Sphinx or MkDocs)

## 🔗 Useful Links

- [uv Documentation](https://docs.astral.sh/uv/)
- [PyPI Publishing Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [Semantic Versioning](https://semver.org/)
- [Python Packaging User Guide](https://packaging.python.org/)

## 🆘 Troubleshooting

### Common Issues:

1. **Import errors**: Make sure all dependencies are properly listed in `pyproject.toml`
2. **Build failures**: Check that all files are properly included
3. **Upload failures**: Verify PyPI credentials and package name availability
4. **Version conflicts**: Ensure version numbers are properly incremented

### Getting Help:

- Check the [uv documentation](https://docs.astral.sh/uv/)
- Review [PyPI packaging guidelines](https://packaging.python.org/)
- Open an issue on the GitHub repository

---

**Your Velaris CSM Access Kit library is ready for deployment! 🎉**
