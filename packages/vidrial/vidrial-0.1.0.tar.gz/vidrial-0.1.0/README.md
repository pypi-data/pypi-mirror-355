# Vidrial
Vidrial is a package for writing non-spaghetti CUDA kernels with just-in-time compilation.

## Build for release
```bash
uv sync --group dev
uv run python build_kernels.py
uv build
```

