import os
from pathlib import Path
from typing import Tuple
from libacbf import ACBFBook


def make_pubinfo_dir(path):
    os.makedirs(path / "metadata/publish_info/", exist_ok=True)
    return path / "metadata/publish_info/"


def test_publisher(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_pubinfo_dir(path)
    with open(dir / "test_publisher.txt", 'w', encoding="utf-8", newline='\n') as result:
        result.write(book.publisher_info.publisher)


def test_publish_date_string(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_pubinfo_dir(path)
    with open(dir / "test_publish_date_string.txt", 'w', encoding="utf-8", newline='\n') as result:
        result.write(book.publisher_info.publish_date_string)


def test_publish_date(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_pubinfo_dir(path)
    with open(dir / "test_publish_date.txt", 'w', encoding="utf-8", newline='\n') as result:
        result.write(str(book.publisher_info.publish_date))


def test_city(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_pubinfo_dir(path)
    with open(dir / "test_city.txt", 'w', encoding="utf-8", newline='\n') as result:
        result.write(book.publisher_info.publish_city)


def test_isbn(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_pubinfo_dir(path)
    with open(dir / "test_isbn.txt", 'w', encoding="utf-8", newline='\n') as result:
        result.write(book.publisher_info.isbn)


def test_license(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_pubinfo_dir(path)
    with open(dir / "test_license.txt", 'w', encoding="utf-8", newline='\n') as result:
        result.write(book.publisher_info.license)
