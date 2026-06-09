import io
import pytest

from fpdf import FPDF
from markitdown import MarkItDown
from markitdown._stream_info import StreamInfo
from markitdown_pdf_pages import PdfConverterWithPage, DocumentConverterResultWithPages


PAGE_TEXTS = [
    "This is page one of the test document.",
    "This is page two of the test document.",
    "This is page three of the test document.",
]

def make_pdf_bytes(page_texts: list[str]) -> bytes:
    """Create a simple multi-page PDF in memory using fpdf2."""
    pdf = FPDF()
    pdf.set_font("Helvetica", size=12)
    for text in page_texts:
        pdf.add_page()
        pdf.cell(0, 10, text)
    return pdf.output()


def test_converter_returns_correct_type() -> None:
    pdf_bytes = make_pdf_bytes(PAGE_TEXTS)
    converter = PdfConverterWithPage()
    result = converter.convert(
        file_stream=io.BytesIO(pdf_bytes),
        stream_info=StreamInfo(mimetype="application/pdf", extension=".pdf"),
    )
    assert isinstance(result, DocumentConverterResultWithPages)


def test_converter_page_count() -> None:
    pdf_bytes = make_pdf_bytes(PAGE_TEXTS)
    converter = PdfConverterWithPage()
    result = converter.convert(
        file_stream=io.BytesIO(pdf_bytes),
        stream_info=StreamInfo(mimetype="application/pdf", extension=".pdf"),
    )
    pages = list(result.markdown_with_pages)
    assert len(pages) == len(PAGE_TEXTS)


def test_converter_page_numbers() -> None:
    pdf_bytes = make_pdf_bytes(PAGE_TEXTS)
    converter = PdfConverterWithPage()
    result = converter.convert(
        file_stream=io.BytesIO(pdf_bytes),
        stream_info=StreamInfo(mimetype="application/pdf", extension=".pdf"),
    )
    page_numbers = [p["page_number"] for p in result.markdown_with_pages]
    assert page_numbers == list(range(1, len(PAGE_TEXTS) + 1))


def test_converter_page_content() -> None:
    pdf_bytes = make_pdf_bytes(PAGE_TEXTS)
    converter = PdfConverterWithPage()
    result = converter.convert(
        file_stream=io.BytesIO(pdf_bytes),
        stream_info=StreamInfo(mimetype="application/pdf", extension=".pdf"),
    )
    pages = list(result.markdown_with_pages)
    for page, expected_text in zip(pages, PAGE_TEXTS):
        assert expected_text in page["markdown"]


def test_markdown_property_populated() -> None:
    pdf_bytes = make_pdf_bytes(PAGE_TEXTS)
    converter = PdfConverterWithPage()
    result = converter.convert(
        file_stream=io.BytesIO(pdf_bytes),
        stream_info=StreamInfo(mimetype="application/pdf", extension=".pdf"),
    )
    for expected_text in PAGE_TEXTS:
        assert expected_text in result.markdown


def test_empty_page_skipped() -> None:
    pdf_bytes = make_pdf_bytes(["First page.", "", "Third page."])
    converter = PdfConverterWithPage()
    result = converter.convert(
        file_stream=io.BytesIO(pdf_bytes),
        stream_info=StreamInfo(mimetype="application/pdf", extension=".pdf"),
    )
    pages = list(result.markdown_with_pages)
    page_numbers = [p["page_number"] for p in pages]
    assert 2 not in page_numbers
    assert 1 in page_numbers
    assert 3 in page_numbers


def test_plugin_loaded_by_markitdown(tmp_path) -> None:
    pdf_bytes = make_pdf_bytes(PAGE_TEXTS)
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(pdf_bytes)

    md = MarkItDown(enable_plugins=True)
    result = md.convert(str(pdf_file))

    assert isinstance(result, DocumentConverterResultWithPages)
    pages = list(result.markdown_with_pages)
    assert len(pages) == len(PAGE_TEXTS)
    for page, expected_text in zip(pages, PAGE_TEXTS):
        assert expected_text in page["markdown"]


def test_markdown_without_touching_pages() -> None:
    pdf_bytes = make_pdf_bytes(PAGE_TEXTS)
    converter = PdfConverterWithPage()
    result = converter.convert(
        file_stream=io.BytesIO(pdf_bytes),
        stream_info=StreamInfo(mimetype="application/pdf", extension=".pdf"),
    )
    md = result.markdown
    for expected_text in PAGE_TEXTS:
        assert expected_text in md


def test_markdown_joins_pages_with_double_newline() -> None:
    pdf_bytes = make_pdf_bytes(PAGE_TEXTS)
    converter = PdfConverterWithPage()
    result = converter.convert(
        file_stream=io.BytesIO(pdf_bytes),
        stream_info=StreamInfo(mimetype="application/pdf", extension=".pdf"),
    )
    assert "\n\n" in result.markdown


def test_markdown_is_cached() -> None:
    pdf_bytes = make_pdf_bytes(PAGE_TEXTS)
    converter = PdfConverterWithPage()
    result = converter.convert(
        file_stream=io.BytesIO(pdf_bytes),
        stream_info=StreamInfo(mimetype="application/pdf", extension=".pdf"),
    )
    first = result.markdown
    second = result.markdown
    assert first is second


def test_markdown_after_partial_iteration() -> None:
    pdf_bytes = make_pdf_bytes(PAGE_TEXTS)
    converter = PdfConverterWithPage()
    result = converter.convert(
        file_stream=io.BytesIO(pdf_bytes),
        stream_info=StreamInfo(mimetype="application/pdf", extension=".pdf"),
    )
    # Only consume the first page
    first_page = next(iter(result.markdown_with_pages))
    assert first_page["page_number"] == 1

    # markdown should still contain all pages, not just the remainder
    md = result.markdown
    for expected_text in PAGE_TEXTS:
        assert expected_text in md


def test_markdown_with_pages_still_works_after_markdown_access() -> None:
    pdf_bytes = make_pdf_bytes(PAGE_TEXTS)
    converter = PdfConverterWithPage()
    result = converter.convert(
        file_stream=io.BytesIO(pdf_bytes),
        stream_info=StreamInfo(mimetype="application/pdf", extension=".pdf"),
    )
    # Access markdown first (drains the generator into the cache)
    _ = result.markdown

    # markdown_with_pages should still yield all pages from the cache
    pages = list(result.markdown_with_pages)
    assert len(pages) == len(PAGE_TEXTS)
    for page, expected_text in zip(pages, PAGE_TEXTS):
        assert expected_text in page["markdown"]
