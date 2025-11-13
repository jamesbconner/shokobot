# GitHub Integration Setup Guide

This guide helps you set up the GitHub Actions CI/CD pipeline for ShokoBot.

## Required Secrets

Add these secrets to your GitHub repository:

### 1. OPENAI_API_KEY (Required for tests)

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `OPENAI_API_KEY`
5. Value: Your OpenAI API key
6. Click **Add secret**

### 2. CODECOV_TOKEN (Optional - for coverage reporting)

1. Sign up at [codecov.io](https://codecov.io)
2. Add your repository
3. Copy the upload token
4. Add as repository secret named `CODECOV_TOKEN`

## Workflows Overview

### test.yml - Automated Testing
- **Triggers:** Push to main/develop, Pull Requests
- **Runs on:** Python 3.12 and 3.13
- **Checks:**
  - Linting with ruff
  - Type checking with mypy
  - Tests with pytest
  - Coverage ≥ 90%
  - Uploads coverage to Codecov

### lint.yml - Code Quality
- **Triggers:** Push to main/develop, Pull Requests
- **Checks:**
  - Code formatting with ruff
  - Linting with ruff

### security.yml - Security Scanning
- **Triggers:** Push to main/develop, Pull Requests, Weekly schedule
- **Checks:**
  - Security vulnerabilities with bandit
  - Uploads security report as artifact

## Dependabot Configuration

Dependabot is configured to:
- Check for Python dependency updates weekly
- Check for GitHub Actions updates weekly
- Create PRs automatically with labels

## Branch Protection (Recommended)

Set up branch protection for `main`:

1. Go to **Settings** → **Branches**
2. Add rule for `main` branch
3. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
     - Select: `test`, `lint`, `security`
   - ✅ Require branches to be up to date before merging
   - ✅ Require conversation resolution before merging

## Status Badges

The README.md already includes status badges:
- Tests status
- Lint status
- Security status
- Codecov coverage
- Python version
- Code style

These will automatically update as workflows run.

## First Run

After pushing these changes:

1. Check the **Actions** tab on GitHub
2. Verify all workflows run successfully
3. Fix any issues that arise
4. Celebrate your automated CI/CD! 🎉

## Troubleshooting

### Tests Fail on GitHub but Pass Locally

- Check that `OPENAI_API_KEY` secret is set
- Verify Python version matches (3.12+)
- Check for environment-specific issues

### Coverage Upload Fails

- Verify `CODECOV_TOKEN` is set correctly
- Check Codecov repository is properly configured
- Review workflow logs for specific errors

### Dependabot PRs Not Appearing

- Ensure dependabot.yml is in `.github/` directory
- Check repository settings allow Dependabot
- Wait for weekly schedule to trigger

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Codecov Documentation](https://docs.codecov.com/)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
