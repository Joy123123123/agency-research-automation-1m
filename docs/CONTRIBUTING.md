# Contributing — Agency Research Automation

## Branch Strategy (GitFlow)

```
main          ← Production-ready, stable code
  └── develop ← Integration branch
        ├── feature/research-engine  ← New features
        ├── feature/ai-scoring       ← New features
        └── staging                  ← Pre-production testing
              └── release/v1.x       ← Release preparation
hotfix        ← Emergency production fixes
```

## How to Contribute

### 1. Fork & Clone

```bash
git clone https://github.com/Joy123123123/agency-research-automation-1m.git
git checkout develop
```

### 2. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Make Changes & Test

```bash
# Run tests
pytest tests/ -v

# Check code style
python -m flake8 src/ --max-line-length 100
```

### 4. Commit

```bash
git add .
git commit -m "feat: add your feature description"
git push origin feature/your-feature-name
```

### 5. Open PR

Open a Pull Request against `develop` branch (not `main`).

## Commit Message Convention

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation
- `test:` — Tests
- `refactor:` — Code refactoring
- `chore:` — Maintenance

## Code Style

- Python: PEP 8, max line length 100
- Use type hints
- Add docstrings to all public functions
- Write tests for new features
