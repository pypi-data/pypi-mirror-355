# SmartDoc CLI

**SmartDoc CLI** is a command-line tool that automatically generates Markdown, HTML, and PDF API documentation for web frameworks like **FastAPI**, **Flask**, and **Django**.

---
## Installation

```bash
pip install smartdoc-cli
```
(For testing with Test PyPI)

`pip install --index-url https://test.pypi.org/simple/ smartdoc
`

---
## Usage
Run this command inside your project directory.

### Example command:
```bash
smartdoc generate \
  --app your_app.main \
  --framework fastapi \
  --output api_docs.md \
  --html \
  --pdf

```
### For FastAPI:
```bash
smartdoc generate --app your_project.main --framework fastapi --output docs.md --html --pdf
```

### For Flask:
```bash
smartdoc generate --app your_project.main --framework flask --output docs.md --html --pdf
```

### For Django:
```bash
smartdoc generate --app your_project.main --framework django --django-settings your_project.settings --output docs.md --html --pdf
```

---
## CLI Options
| Option               | Description                                       |
| -------------------- | ------------------------------------------------- |
| `--app` / `-a`       | Python path to your app module                    |
| `--framework` / `-f` | One of `fastapi`, `flask`, `django`               |
| `--output` / `-o`    | Output Markdown filename (default: `api_docs.md`) |
| `--html`             | Generate HTML output                              |
| `--pdf`              | Generate PDF output                               |
| `--django-settings`  | Required for Django to specify settings module    |

---
## Output

Depending on options used:

`api_docs.md` — default markdown output

`api_docs.html` — HTML format (with `--html`)

`api_docs.pdf` — PDF format (with `--pdf`)

---
## Author
Built with 💻 by **Mohammad Safwan Athar** [@DevSaifOps](https://github.com/Dev-Saif-Ops)

---
## License

This project is licensed under the MIT License.

---

```txt
MIT License

Copyright (c) 2025 Mohammad Safwan Athar aka DevSaifOps

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
