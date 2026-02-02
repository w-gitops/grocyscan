# Appendix E: User Documentation (GitHub Pages)

## E.1 Overview

GrocyScan documentation is hosted on GitHub Pages using MkDocs with the Material theme.

## E.2 Documentation Structure

```
docs/
├── mkdocs.yml                    # MkDocs configuration
├── docs/
│   ├── index.md                  # Home page
│   ├── getting-started/
│   │   ├── installation.md
│   │   ├── configuration.md
│   │   ├── first-scan.md
│   │   └── docker-setup.md
│   ├── user-guide/
│   │   ├── scanning.md
│   │   ├── products.md
│   │   ├── locations.md
│   │   ├── expiration.md
│   │   └── settings.md
│   ├── integrations/
│   │   ├── grocy.md
│   │   ├── llm-providers.md
│   │   ├── lookup-providers.md
│   │   ├── n8n.md
│   │   └── mcp.md
│   ├── api/
│   │   ├── overview.md
│   │   ├── authentication.md
│   │   ├── endpoints.md
│   │   └── examples.md
│   ├── development/
│   │   ├── contributing.md
│   │   ├── architecture.md
│   │   ├── testing.md
│   │   └── standards.md
│   ├── troubleshooting.md
│   └── changelog.md
└── requirements-docs.txt
```

## E.3 MkDocs Configuration

```yaml
# mkdocs.yml
site_name: GrocyScan Documentation
site_url: https://yourusername.github.io/grocyscan
repo_url: https://github.com/yourusername/grocyscan

theme:
  name: material
  features:
    - navigation.instant
    - navigation.tabs
    - navigation.sections
    - search.suggest
    - content.code.copy
  palette:
    - scheme: default
      primary: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode

plugins:
  - search
  - git-revision-date-localized

markdown_extensions:
  - admonition
  - pymdownx.highlight
  - pymdownx.superfences
  - pymdownx.tabbed
```

## E.4 GitHub Actions Deployment

```yaml
# .github/workflows/docs.yml
name: Deploy Documentation

on:
  push:
    branches: [main]
    paths: ['docs/**']

permissions:
  contents: write
  pages: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - run: pip install -r requirements-docs.txt
      - run: mkdocs build --strict

      - uses: actions/deploy-pages@v4
```

## E.5 Local Development

```bash
# Install dependencies
pip install -r requirements-docs.txt

# Serve locally with hot-reload
mkdocs serve

# Build documentation
mkdocs build

# Deploy to GitHub Pages
mkdocs gh-deploy --force
```

## E.6 Documentation Dependencies

```text
# requirements-docs.txt
mkdocs>=1.5.3
mkdocs-material>=9.5.0
mkdocs-git-revision-date-localized-plugin>=1.2.2
pymdown-extensions>=10.7
```

---

## Navigation

- **Previous:** [Appendix D - Troubleshooting](appendix-d-troubleshooting.md)
- **Next:** [Appendix F - n8n Integration](appendix-f-n8n-integration.md)
- **Back to:** [README](README.md)
