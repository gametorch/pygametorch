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
`index = testpypi`. This builds, validates and uploads to TestPyPI. It does not
tag or create a release.

Verify a real install in a throwaway environment:

```sh
uv venv /tmp/gt-check --python 3.14
uv pip install --python /tmp/gt-check \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ pygametorch
uv run --python /tmp/gt-check python -c "import gametorch; print(gametorch.__version__)"
```

## 3. Release to PyPI

Pushing the version bump to `main` is all it takes. The Publish workflow runs on
any push that changes `src/gametorch/_version.py`, and once the bump lands it:

1. builds and validates the distributions,
2. publishes them to PyPI via OIDC, then
3. creates the `vX.Y.Z` tag and a GitHub Release with generated notes.

The tag is created **after** a successful publish, so a tagged version is always
on PyPI, and the job is skipped entirely when the tag already exists — re-pushing
`main` won't re-release.

Two manual fallbacks remain if you need them:

- Create a GitHub Release with a tag matching the version (for example `v0.1.1`);
  publishing it triggers the `publish-pypi` job.
- Run the workflow manually with `index = pypi`.

## Notes

- **Versions are immutable.** A filename (`pygametorch-0.1.1-*.whl`) can never be
  re-uploaded. To fix a bad release, yank it on PyPI and publish a new patch
  version.
- **Only CI creates release tags.** Don't push `vX.Y.Z` by hand — the automated
  flow keys off the tag's absence, and a pre-existing tag makes it skip the
  release.
- The `release: published` and manual `workflow_dispatch` paths still exist, but
  the push-on-bump path is the normal one.
- The workflow runs `uvx twine check dist/*` before uploading, so a broken
  README/metadata fails fast.
- To publish locally as a fallback (requires an API token):
  `UV_PUBLISH_TOKEN=pypi-... uv publish`.
