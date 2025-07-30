# Build Instructions

Follow these steps to build and publish the SDK.

---

## 1. Install [UV](https://github.com/astral-sh/uv)

Recommended: Install using [pipx](https://pypa.github.io/pipx/):

```sh
pipx install uv
```

Alternatively, install globally with pip:

```sh
pip install uv
```

---

## 2. Sync Dependencies

Install all dependencies listed in `pyproject.toml`:

```sh
uv sync
```

---

## 3. Run Tests

Run tests using [pytest](https://docs.pytest.org/):

```sh
uv run pytest
```

---

## 4. Add Build Tools

Add the `build` tool as a development dependency:

```sh
uv add --dev build
```

---

## 5. Build the SDK

Build the SDK package:

```sh
uv run python -m build
```

---

## 6. Publish to PyPI

Add [twine](https://twine.readthedocs.io/) as a development dependency:

```sh
uv add --dev twine
```

Upload the built package to PyPI:

```sh
uv run twine upload dist/*
```
