'''
Custom MarkItDown plugin that provides a PDF converter which extracts text 
on a per-page basis and includes page numbers in the output. 
Implementation based off https://github.com/microsoft/markitdown/blob/4a5340f93b2bf1dc11641f921fbfd6d5f016924b/packages/markitdown-sample-plugin/README.md
'''

import sys
import io
from typing import BinaryIO, Any, Generator

from markitdown import MarkItDown
from markitdown._base_converter import DocumentConverterResult
from markitdown._stream_info import StreamInfo
from markitdown._exceptions import MissingDependencyException, MISSING_DEPENDENCY_MESSAGE
from markitdown.converters._pdf_converter import (
    PdfConverter,
    _extract_form_content_from_words,
    _merge_partial_numbering_lines,
)

_dependency_exc_info = None
try:
    import pdfplumber
except ImportError:
    _dependency_exc_info = sys.exc_info()


__plugin_interface_version__ = 1  # required by MarkItDown's plugin interface


def register_converters(markitdown: MarkItDown, **kwargs) -> None:
    """
    Plugin converters are inserted ahead of built-ins,
    so this behavior takes precedence for PDFs.
    """
    markitdown.register_converter(PdfConverterWithPage())


class DocumentConverterResultWithPages(DocumentConverterResult):
    """
    Extends DocumentConverterResult with per-page access via markdown_with_page_cache.
    - Iterating markdown_with_page_cache pulls pages from the generator one at a time.
    - Accessing markdown (e.g. from the CLI) drains the remaining generator and
      joins all pages, then caches the result for subsequent accesses.

    """

    def __init__(
        self,
        markdown_with_page_cache: Generator[dict[str, Any], None, None],
    ):
        self._gen = markdown_with_page_cache
        self._page_cache: list[dict[str, Any]] = []
        self._exhausted: bool = False
        self._markdown_cache: str | None = None
        self._init_done: bool = False
        super().__init__("")
        self._init_done = True


    def _pull_next(self) -> None:
        try:
            self._page_cache.append(next(self._gen))
        except StopIteration:
            self._exhausted = True

    @property
    def markdown(self) -> str:
        if self._markdown_cache is None:
            while not self._exhausted:
                self._pull_next()
            self._markdown_cache = "\n\n".join(p["markdown"] for p in self._page_cache)
        return self._markdown_cache

    @markdown.setter
    def markdown(self, value: str) -> None:
        if not getattr(self, "_init_done", False):
            return
        self._markdown_cache = value

    @property
    def markdown_with_pages(self) -> Generator[dict[str, Any], None, None]:
        idx = 0
        while True:
            if idx < len(self._page_cache):
                yield self._page_cache[idx]
                idx += 1
            elif self._exhausted:
                return
            else:
                self._pull_next()


class PdfConverterWithPage(PdfConverter):
    """
    Converts a PDF file to markdown using pdfplumber, extracting text on a
    per-page basis and including page numbers in the output.
    """

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResultWithPages:
        if _dependency_exc_info is not None:
            raise MissingDependencyException(
                MISSING_DEPENDENCY_MESSAGE.format(
                    converter=type(self).__name__,
                    extension=".pdf",
                    feature="pdf",
                )
            ) from _dependency_exc_info[1].with_traceback(_dependency_exc_info[2])

        assert isinstance(file_stream, io.IOBase)

        pdf_bytes = io.BytesIO(file_stream.read())

        def page_generator() -> Generator[dict[str, Any], None, None]:
            with pdfplumber.open(pdf_bytes) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_content = _extract_form_content_from_words(page)

                    if page_content is None:
                        text = page.extract_text()
                        if text and text.strip():
                            yield {
                                "page_number": i + 1,
                                "markdown": _merge_partial_numbering_lines(text.strip()),
                            }
                    else:
                        if page_content.strip():
                            yield {
                                "page_number": i + 1,
                                "markdown": page_content.strip(),
                            }

        return DocumentConverterResultWithPages(
            markdown_with_page_cache=page_generator(),
        )
