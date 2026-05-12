# ShadowAudit Documentation

Welcome to the ShadowAudit documentation site.

## Local development

Activate the project's virtual environment (optional but recommended):

```bash
source .venv/bin/activate
```

Start the live preview server:

```bash
.venv/bin/mkdocs serve
# or
/Users/anshumankumar/Documents/shadowaudit-python/.venv/bin/python -m mkdocs serve
```

Open http://127.0.0.1:8000 in your browser.

## Build for production

Build the static site to the `site/` directory:

```bash
.venv/bin/mkdocs build
# or
/Users/anshumankumar/Documents/shadowaudit-python/.venv/bin/python -m mkdocs build
```

The generated site will be in the `site/` folder.
