# markitdown-pdf-pages

A [MarkItDown](https://github.com/microsoft/markitdown) plugin that converts PDFs to markdown on a per-page basis, yielding each page's content along with its page number.

## Installation

```bash
pip install git+https://github.com/samconibear/markitdown-pdf-pages.git
```


Verify the plugin is installed:

```bash
markitdown --list-plugins
```

## Usage

### Command line

```bash
markitdown --use-plugins document.pdf
```

### Python

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=True)
result = md.convert("document.pdf")

# Iterate over pages
for page in result.markdown_with_pages:
    print(f"--- Page {page['page_number']} ---")
    print(page['markdown'])
# Output:
# --- Page 1 ---
# This is the text from page one.
# --- Page 2 ---
# This is the text from page two.


# The standard MarkItDown implementation still works the same
print(result.markdown)
# Output:
# This is the text from page one.
# This is the text from page two.
```

## How it works

The plugin registers a `PdfConverterWithPage` that takes priority over MarkItDown's built-in PDF converter. It uses `pdfplumber` to extract text page-by-page, returning a `DocumentConverterResultWithPages` whose `markdown_with_pages` attribute is a generator of `{"page_number": int, "markdown": str}` dicts.

## Run the tests:
```bash
pip install -e ".[test]"
pytest -v
```