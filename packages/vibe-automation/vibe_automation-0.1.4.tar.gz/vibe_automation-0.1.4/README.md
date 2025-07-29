# Vibe Automation SDK

## Development Setup

### Prerequisites
- Python >=3.13
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

1. Install uv if you haven't already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

### Running Examples

```bash
uv run python examples/form.py
```

## Release Process

To create a new release:

1. Create and push a release tag:
   ```bash
   git tag release/v0.1.2
   git push origin release/v0.1.2
   ```

2. This will automatically:
   - Create a GitHub release with auto-generated release notes
   - Build the package using `uv build`
   - Publish to PyPI using OpenID Connect (trusted publishing)

The release workflow is configured to trigger on tags matching `release/v*` pattern.
