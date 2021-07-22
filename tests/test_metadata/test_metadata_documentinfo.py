import os
import json
from pathlib import Path
from typing import Tuple
from tests.conftest import get_au_op
from libacbf import ACBFBook


def make_docinfo_dir(path):
    os.makedirs(path / "metadata/document_info/", exist_ok=True)
    return path / "metadata/document_info/"


def test_authors(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    op = [get_au_op(x) for x in book.Metadata.document_info.authors]
    dir = make_docinfo_dir(path)
    with open(dir / "test_authors.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_creation_date_string(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_docinfo_dir(path)
    with open(dir / "test_creation_date_string.txt", 'w', encoding="utf-8", newline='\n') as result:
        result.write(book.Metadata.document_info.creation_date_string)


def test_creation_date(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_docinfo_dir(path)
    with open(dir / "test_creation_date.txt", 'w', encoding="utf-8", newline='\n') as result:
        result.write(str(book.Metadata.document_info.creation_date))


def test_source(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_docinfo_dir(path)
    with open(dir / "test_source.txt", 'w', encoding="utf-8", newline='\n') as result:
        result.write(book.Metadata.document_info.source)


def test_id(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_docinfo_dir(path)
    with open(dir / "test_id.txt", 'w', encoding="utf-8", newline='\n') as result:
        result.write(book.Metadata.document_info.document_id)


def test_version(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_docinfo_dir(path)
    with open(dir / "test_version.txt", 'w', encoding="utf-8", newline='\n') as result:
        result.write(book.Metadata.document_info.document_version)


def test_history(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_docinfo_dir(path)
    with open(dir / "test_history.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(book.Metadata.document_info.document_history, ensure_ascii=False, indent='\t',
                                separators=(', ', ': ')))
