<div align="center">

# 🌌 aeoncord

### Elegant Discord API client

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-ARR-F5C518?style=for-the-badge)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000?style=for-the-badge&logo=python&logoColor=white)](https://github.com/psf/black)
[![Lint](https://img.shields.io/badge/lint-ruff-D7FF64?style=for-the-badge&logo=ruff&logoColor=black)](https://github.com/astral-sh/ruff)
[![Type Check](https://img.shields.io/badge/types-mypy-2A6DB2?style=for-the-badge)](https://github.com/python/mypy)
[![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org/)
[![uv](https://img.shields.io/badge/package%20manager-uv-DE5FE9?style=for-the-badge&logo=astral&logoColor=white)](https://github.com/astral-sh/uv)

<br>

**A modern, elegant and fast Discord API client built with Python.**

</div>

---

## ✨ Features

- 🚀 Modern async-first architecture
- 🧩 Clean and extensible API
- ⚡ Fast dependency management with `uv`
- 🛡️ Type-safe development workflow
- 🧪 Built-in testing and linting support

---

## 📦 Installation

### Using `uv` (recommended)

```bash
git clone https://github.com/mrf0rtuna4/aeoncord.git

cd aeoncord

uv sync --all-extras
````

Activate the environment:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

---

### Using pip

```bash
git clone https://github.com/mrf0rtuna4/aeoncord.git

cd aeoncord

python -m venv venv

source venv/bin/activate
# Windows: venv\Scripts\activate

pip install -e ".[dev]"
```

---

## 🛠 Development

Run checks locally:

```bash
ruff check .
ruff format --check .
mypy .
pytest
```

Or with `uv`:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

---

## 📄 License

ARR © mr_fortuna
