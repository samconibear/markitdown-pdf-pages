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

## Use in RAG pipelines
A core challenge in Retrieval Augmented Generation (RAG) is source transparency - when a system returns an answer, users need to know exactly where it came from.This is especially critical in domains where trust and verifiability are essential, such as legal, compliance, technical documentation, and academic research.
This plugin attaches a page number to every chunk at extraction time, so the reference is never lost as content flows through your pipeline:
```python
from markitdown import MarkItDown
from your_vector_store import embed

md = MarkItDown(enable_plugins=True)
result = md.convert("report.pdf")

for page in result.markdown_with_pages:
    embed(
        text=page["markdown"],
        metadata={
            "source": "report.pdf",
            "page": page["page_number"],  # cited in every retrieval result
        }
    )
```
When a retrieved chunk is used to generate an answer, the page number surfaces as a citation.
Pages can serve as natural chunking     boundaries, as they often contain a single coherent topic. For more complex documents, I suggest using a structure-aware splitter like LangChain's [MarkdownTextSplitter](https://docs.langchain.com/oss/python/integrations/splitters/markdown_header_metadata_splitter) which can create more accurate chunks based on document headings and sections.

## How it works

The plugin registers a `PdfConverterWithPage` that takes priority over MarkItDown's built-in PDF converter. It uses `pdfplumber` to extract text page-by-page, returning a `DocumentConverterResultWithPages` whose `markdown_with_pages` attribute is a generator of `{"page_number": int, "markdown": str}` dicts.

## Run the tests:
```bash
pip install -e ".[test]"
pytest -v
```