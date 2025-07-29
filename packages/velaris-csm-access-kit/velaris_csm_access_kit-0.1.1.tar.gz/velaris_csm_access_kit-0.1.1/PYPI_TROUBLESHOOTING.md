# PyPI Upload Troubleshooting Guide

## 🚨 Current Issue: 403 Forbidden Error

The error you're seeing indicates authentication problems. Here's how to fix it:

### Issue 1: TestPyPI vs PyPI Tokens

**Problem**: You're using a PyPI token for TestPyPI upload.

**Solution**: You need separate accounts and tokens:

1. **For TestPyPI** (testing):
   - Create account at: https://test.pypi.org/account/register/
   - Create API token at: https://test.pypi.org/manage/account/token/

2. **For PyPI** (production):
   - Create account at: https://pypi.org/account/register/
   - Create API token at: https://pypi.org/manage/account/token/

### Issue 2: Multiple Distribution Files

Your `dist/` folder contains multiple versions:
- `velaris_csm_access_kit-0.1.0-py3-none-any.whl`
- `velaris_csm_access_kit-0.1.1.dev0+gbe4a264.d20250613-py3-none-any.whl`
- `velaris_csm_access_kit-0.1.0.tar.gz`
- `velaris_csm_access_kit-0.1.1.dev0+gbe4a264.d20250613.tar.gz`

**Solution**: Clean the dist folder and rebuild:

```bash
# Clean old builds
rm -rf dist/
rm -rf build/

# Rebuild with current version
uv build
```

### Step-by-Step Fix

#### Step 1: Create TestPyPI Account
1. Go to https://test.pypi.org/account/register/
2. Create a new account (separate from PyPI)
3. Verify your email

#### Step 2: Create TestPyPI API Token
1. Go to https://test.pypi.org/manage/account/token/
2. Create a new API token
3. Copy the full token (including `pypi-` prefix)

#### Step 3: Set Up Credentials
Run the credential setup script:
```bash
python setup_pypi_credentials.py
```

Or manually create `~/.pypirc`:
```ini
[distutils]
index-servers = 
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PYPI_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_TOKEN_HERE
```

#### Step 4: Clean and Rebuild
```bash
cd velaris_csm_access_kit
rm -rf dist/ build/
uv build
```

#### Step 5: Upload to TestPyPI
```bash
uv run twine upload --repository testpypi dist/*
```

### Alternative: Direct Token Method

If you prefer not to use `.pypirc`, you can pass credentials directly:

```bash
uv run twine upload --repository testpypi \
  --username __token__ \
  --password pypi-YOUR_TESTPYPI_TOKEN_HERE \
  dist/*
```

### Verification

After successful upload, test installation:
```bash
# In a new directory
uv add --index-url https://test.pypi.org/simple/ velaris-csm-access-kit
```

### Common Issues

1. **Package name already exists**: Try a different name like `velaris-csm-access-kit-yourname`
2. **Token format**: Ensure token includes `pypi-` prefix
3. **Account mismatch**: TestPyPI and PyPI are separate - need separate accounts
4. **File permissions**: Ensure `.pypirc` has correct permissions (600)

### Next Steps

1. ✅ Fix TestPyPI upload
2. ✅ Test installation from TestPyPI
3. ✅ Create PyPI account and token
4. ✅ Upload to production PyPI
