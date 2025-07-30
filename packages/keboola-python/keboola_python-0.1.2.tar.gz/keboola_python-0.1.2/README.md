# keboola-python

Shared utility code for Keboola Python components.

---

## 🛠️ Setup for Developers

Follow these steps to get up and running:

### 1. Clone the repo

```bash
git clone https://github.com/emfoundation/keboola-python.git
cd keboola-python
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dev dependencies

```bash
pip install -r requirements-dev.txt
```

This will install tools like:
- `black` (auto-formatting)
- `flake8` (linting)
- `pre-commit` (to run checks before each commit)
- `pytest` (for tests)

---

## 🧪 Pre-Commit Hook Setup

We use [`pre-commit`](https://pre-commit.com) to run formatting and linting checks automatically on every commit.

### Install the hook, from within your virtual environment (one-time setup)

```bash
pre-commit install
```

### Try it out

Make a code change and run:

```bash
git add .
git commit -m "Trigger pre-commit"
```

You'll see `black` and `flake8` run before the commit is saved.
