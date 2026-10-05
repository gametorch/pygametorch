# Releasing

The PyPI project is **`pygametorch`** (import name `gametorch`). Releases are
published from GitHub Actions using [Trusted
Publishing](https://docs.pypi.org/trusted-publishers/) — no API tokens are
stored anywhere.

## One-time setup (already configured)

Pending Trusted Publishers are registered on both indexes for:

- Repository: `gametorch/pygametorch`
- Workflow: `workflow.yml` (must match `.github/workflows/workflow.yml`)
- Environment: `testpypi` (TestPyPI) / `pypi` (PyPI)

Make sure the GitHub environments named `testpypi` and `pypi` exist under
**Settings → Environments** (GitHub creates them on first use, but you may want
to add required reviewers on `pypi`).

## 1. Bump the version

The single source of truth is `src/gametorch/_version.py`:

```python
__version__ = "0.1.1"
```

hatchling reads it via `[tool.hatch.version]` in `pyproject.toml`, so nothing
else needs editing.

```sh
# sanity check: the built artifact picks up the new version
uv build && ls dist/
```

Commit the bump:

```sh
git commit -am "Release 0.1.1"
git push origin main
```

## 2. Test on TestPyPI

Run the **Publish** workflow manually (`Actions → Publish → Run workflow`) with
`index = testpypi`. This builds, validates and uploads to TestPyPI.

Verify a real install in a throwaway environment:

```sh
uv venv /tmp/gt-check --python 3.14
uv pip install --python /tmp/gt-check \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ pygametorch
uv run --python /tmp/gt-check python -c "import gametorch; print(gametorch.__version__)"
```

## 3. Release to PyPI

Create a GitHub Release with a tag matching the version (for example `v0.1.1`).
Publishing the release triggers the workflow's `publish-pypi` job, which uploads
to PyPI via OIDC.

Alternatively, run the workflow manually with `index = pypi`.

## Notes

- **Versions are immutable.** A filename (`pygametorch-0.1.1-*.whl`) can never be
  re-uploaded. To fix a bad release, yank it on PyPI and publish a new patch
  version.
- The workflow runs `uvx twine check dist/*` before uploading, so a broken
  README/metadata fails fast.
- To publish locally as a fallback (requires an API token):
  `UV_PUBLISH_TOKEN=pypi-... uv publish`.
