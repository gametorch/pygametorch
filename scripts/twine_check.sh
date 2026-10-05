#!/usr/bin/env bash
# Build the sdist + wheel into a temporary directory and validate their
# metadata and long-description rendering with twine. Mirrors the pre-upload
# check in .github/workflows/workflow.yml, without clobbering ./dist.
set -euo pipefail

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

uv build --out-dir "$tmp" >/dev/null
uvx twine check "$tmp"/*
