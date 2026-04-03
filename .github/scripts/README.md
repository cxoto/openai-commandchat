# Version Check for PyPI Publishing

This directory contains scripts to check if the package version has changed before publishing to PyPI.

## Quick Start

### For Users/Maintainers

**To publish a new version:**

1. Update version in `pyproject.toml`:
   ```toml
   version = "0.0.14"  # Increment from current version
   ```

2. Commit and push to master:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.0.14"
   git push origin master
   ```

3. GitHub Actions will automatically:
   - Check if version changed
   - Build and publish to PyPI (only if version changed)

**If version hasn't changed:**
- GitHub Actions will skip publishing
- You'll see a warning in the workflow logs
- No error - the workflow completes successfully

## Files

- `check_version.py` - Python script that compares local version with PyPI version
- `requirements.txt` - Dependencies for the version check script
- `VERSION_CHECK.md` - Detailed documentation

## How It Works

```
┌─────────────────────┐
│  Push to master     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Check version       │
│ (compare with PyPI) │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌─────────┐ ┌─────────┐
│ Changed │ │Same Ver │
└────┬────┘ └────┬────┘
     │           │
     ▼           ▼
┌─────────┐ ┌─────────┐
│ Publish │ │  Skip   │
│ to PyPI │ │ Publish │
└─────────┘ └─────────┘
```

## Testing Locally

```bash
# Install dependencies
pip install -r .github/scripts/requirements.txt

# Run version check
python .github/scripts/check_version.py

# Check exit code
echo $?
# 0 = version changed (ready to publish)
# 1 = version not changed (skip publish)
# 2 = error occurred
```

## Example Output

**Version changed:**
```
Local version: 0.0.14
PyPI version: 0.0.13
✅ Version changed from 0.0.13 to 0.0.14. Ready to publish.
```

**Version not changed:**
```
Local version: 0.0.13
PyPI version: 0.0.13
❌ Version 0.0.13 has not changed. Skipping publish.
```

## Troubleshooting

**Q: Workflow completes but nothing is published**
- Check if you updated the version in `pyproject.toml`
- Look for the warning message in workflow logs

**Q: Want to force publish without version change**
- Not recommended (PyPI rejects duplicate versions)
- If necessary, temporarily modify the workflow file

**Q: First time publishing**
- Version check will pass automatically
- Package doesn't exist on PyPI yet

## See Also

- [Detailed Documentation](VERSION_CHECK.md)
- [GitHub Actions Workflow](../workflows/publish-to-pypi.yml)
- [PyPI Project Page](https://pypi.org/project/commandchat/)

