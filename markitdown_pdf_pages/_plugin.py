'''
Custom MarkItDown plugin that provides a PDF converter which extracts text 
on a per-page basis and includes page numbers in the output. 
Implementation based off https://github.com/microsoft/markitdown/blob/4a5340f93b2bf1dc11641f921fbfd6d5f016924b/packages/markitdown-sample-plugin/README.md
'''

from concurrent.futures import ThreadPoolExecutor
import sys
import io
from threading import Thread
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
    so this behavior takes presedence for PDFs.
    """
    markitdown.register_converter(PdfConverterWithPage())

class DocumentConverterResultWithPages(DocumentConverterResult):
    def __init__(
        self,
        markdown: str,
        markdown_with_pages: Generator[dict[str, Any], None, None]
    ):
        super().__init__(markdown)
        self.markdown_with_pages: Generator[dict[str, Any], None, None] = markdown_with_pages

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

        # Read file stream into BytesIO for compatibility with pdfplumber
        pdf_bytes = io.BytesIO(file_stream.read())

        def page_generator():
          with pdfplumber.open(pdf_bytes) as pdf:
              for i, page in enumerate(pdf.pages):
                  # form-style word position extraction
                  page_content = _extract_form_content_from_words(page)

                  page_md = page.extract_text() or ""
                  page_md = _merge_partial_numbering_lines(page_md)
                  
                  # If extraction returns None, this page is not form-style
                  if page_content is None:
                      # Extract text using pdfplumber's basic extraction for this page
                      text = page.extract_text()
                      if text and text.strip():
                          yield {
                              "page_number": i + 1,
                              "markdown": text.strip(),
                          }
                  else:
                      if page_content.strip():
                          yield {
                              "page_number": i + 1,
                              "markdown": page_content.strip(),
                          }

        return DocumentConverterResultWithPages(
            markdown='',
            markdown_with_pages=page_generator()
        )


    def convert_parallel(
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

        # Read file stream into BytesIO for compatibility with pdfplumber
        pdf_bytes = io.BytesIO(file_stream.read())

        def process_page(i, page):
            # form-style word position extraction
            page_content = _extract_form_content_from_words(page)

            page_md = page.extract_text() or ""
            page_md = _merge_partial_numbering_lines(page_md)
            
            # If extraction returns None, this page is not form-style
            r = None
            if page_content is None:
                # Extract text using pdfplumber's basic extraction for this page
                text = page.extract_text()
                if text and text.strip():
                    r = {
                        "page_number": i + 1,
                        "markdown": text.strip(),
                    }
            else:
                if page_content.strip():
                    r = {
                        "page_number": i + 1,
                        "markdown": page_content.strip(),
                    }
            return r
            raise ValueError(f"Page {i+1} has no extractable content")
            
        with pdfplumber.open(pdf_bytes) as pdf:
            from multiprocessing import Pool
            with Pool() as exec:
                result = exec.map(process_page, list(*enumerate(pdf.pages)))
                return DocumentConverterResultWithPages(
                    markdown='',
                    markdown_with_pages=result
                )