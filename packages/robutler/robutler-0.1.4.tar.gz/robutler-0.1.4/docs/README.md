# Robutler Documentation

This directory contains the source files for the Robutler documentation website, built with [MkDocs](https://www.mkdocs.org/) and [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).

## Quick Start

### Prerequisites
- Python 3.10+
- pip

### Local Development
1. Install dependencies: `pip install -r docs/requirements.txt`
2. Serve locally: `mkdocs serve`
3. Open [http://localhost:8000](http://localhost:8000)

## Structure

```
docs/
├── index.md                    # Homepage
├── getting-started/            # Getting started guides
├── guides/                     # Detailed guides
├── examples/                   # Working examples
├── reference/                  # API reference (auto-generated)
├── assets/                     # Images, logos, etc.
├── stylesheets/               # Custom CSS
└── includes/                  # Reusable snippets
```

## Building

- Local: `mkdocs serve`
- Production: `mkdocs build --clean --strict`
- Auto-deploy: Pushes to main branch deploy to GitHub Pages

## Contributing

1. Create Markdown files in appropriate directories
2. Add to navigation in `mkdocs.yml`
3. Follow existing style and structure
4. Test locally before submitting

For more details, see the full documentation at the generated site. 