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

## Use case: RAG pipelines

Most PDF converters return a single block of text, which is too coarse for retrieval-augmented generation (RAG). Splitting that block into fixed-size chunks loses structural information — a chunk boundary might land mid-sentence, or merge content from two unrelated sections.

Pages are a natural chunk boundary. They match how humans reference documents (*"see page 12"*), and they tend to contain one coherent topic. This plugin exposes page numbers as first-class metadata, so each page can be stored as a discrete vector with a citable source:

```python
from markitdown import MarkItDown
from your_vector_store import embed_and_upsert

md = MarkItDown(enable_plugins=True)
result = md.convert("report.pdf")

for page in result.markdown_with_pages:   # streams lazily — memory-efficient
    embed_and_upsert(
        text=page["markdown"],
        metadata={
            "source": "report.pdf",
            "page": page["page_number"],  # store for retrieval and citation
        }
    )
```

When a query retrieves a chunk, the page number travels with it, so the system can tell the user exactly where to look. This is especially valuable in domains where citations matter — legal, compliance, technical manuals, academic research — but useful any time you want users to be able to verify an AI-generated answer against the source document.

## How it works

The plugin registers a `PdfConverterWithPage` that takes priority over MarkItDown's built-in PDF converter. It uses `pdfplumber` to extract text page-by-page, returning a `DocumentConverterResultWithPages` whose `markdown_with_pages` attribute is a generator of `{"page_number": int, "markdown": str}` dicts.

## Run the tests:
```bash
pip install -e ".[test]"
pytest -v
```