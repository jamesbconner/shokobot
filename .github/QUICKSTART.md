# GitHub Integration Quick Start

## ✅ What's Been Set Up

### Automated Workflows
- ✅ **Tests** - Run on every push/PR (Python 3.12 & 3.13)
- ✅ **Lint** - Code quality checks with ruff
- ✅ **Security** - Weekly security scans with bandit
- ✅ **Dependabot** - Automated dependency updates

### Templates
- ✅ Pull Request template
- ✅ Bug report template
- ✅ Feature request template

### Documentation
- ✅ CONTRIBUTING.md - Contributor guidelines
- ✅ README.md - Updated with badges and CI/CD info
- ✅ Setup guide - Detailed configuration instructions

## 🚀 Next Steps

### 1. Add GitHub Secrets (Required)

```bash
# Go to: Settings → Secrets and variables → Actions
# Add: OPENAI_API_KEY (required for tests)
# Add: CODECOV_TOKEN (optional, for coverage reporting)
```

### 2. Push to GitHub

```bash
git add .github/ CONTRIBUTING.md README.md
git commit -m "ci: add GitHub Actions CI/CD pipeline"
git push origin main
```

### 3. Verify Workflows

1. Go to **Actions** tab on GitHub
2. Watch workflows run automatically
3. Check that all pass ✅

### 4. Set Up Branch Protection (Recommended)

```
Settings → Branches → Add rule for 'main'
- Require PR before merging
- Require status checks: test, lint, security
- Require up-to-date branches
```

## 📊 What Gets Checked

Every PR will automatically check:
- ✅ All 380+ tests pass
- ✅ Coverage stays ≥ 90%
- ✅ Code is formatted (ruff)
- ✅ No linting errors (ruff)
- ✅ Type checking passes (mypy)
- ✅ No security issues (bandit)

## 🎯 For Contributors

### Before Submitting PR

```bash
# Run locally to match CI checks
poetry run ruff format .
poetry run ruff check . --fix
poetry run pytest --cov --cov-fail-under=90
poetry run mypy services/ utils/ models/ --ignore-missing-imports
```

### PR Process

1. Create feature branch
2. Make changes with tests
3. Run checks locally
4. Push and create PR
5. Wait for CI checks ✅
6. Address review feedback
7. Merge when approved

## 📈 Monitoring

### Status Badges (in README)
- Tests: ![Tests](https://github.com/jamesbconner/shokobot/actions/workflows/test.yml/badge.svg)
- Lint: ![Lint](https://github.com/jamesbconner/shokobot/actions/workflows/lint.yml/badge.svg)
- Security: ![Security](https://github.com/jamesbconner/shokobot/actions/workflows/security.yml/badge.svg)
- Coverage: ![codecov](https://codecov.io/gh/jamesbconner/shokobot/branch/main/graph/badge.svg)

### Where to Check
- **Actions tab** - Workflow runs and logs
- **Pull Requests** - Status checks on PRs
- **Codecov** - Detailed coverage reports
- **Security tab** - Dependabot alerts

## 🔧 Customization

### Adjust Coverage Threshold
Edit `.github/workflows/test.yml`:
```yaml
--cov-fail-under=90  # Change to desired percentage
```

### Add More Python Versions
Edit `.github/workflows/test.yml`:
```yaml
python-version: ["3.12", "3.13", "3.14"]  # Add versions
```

### Change Schedule
Edit `.github/workflows/security.yml`:
```yaml
cron: '0 0 * * 0'  # Weekly on Sunday
```

## 📚 Documentation

- **Full Setup Guide**: `.github/SETUP.md`
- **Contributing Guide**: `CONTRIBUTING.md`
- **README**: Updated with CI/CD section

## 🎉 You're All Set!

Your repository now has:
- Automated testing on every change
- Code quality enforcement
- Security scanning
- Dependency management
- Professional templates
- Clear contribution guidelines

Happy coding! 🚀
