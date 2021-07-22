import os
from pathlib import Path
from libacbf import ACBFBook

edit_dir = Path("tests/results/edit_meta/publish_info/")
os.makedirs(edit_dir, exist_ok=True)


def test_publisher():
    with ACBFBook(edit_dir / "test_publisher.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Publisher")
        book.Metadata.publisher_info.set_publisher("Grafcube")


def test_publish_date():
    with ACBFBook(edit_dir / "test_publish_date.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Publish Date")
        book.Metadata.publisher_info.set_publish_date("1st Jan, 2021")


def test_publish_date_excl():
    with ACBFBook(edit_dir / "test_publish_date_excl.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Publish Date No ISO")
        book.Metadata.publisher_info.set_publish_date("2nd Jan, 2021", include_date=False)


def test_city():
    with ACBFBook(edit_dir / "test_city.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Publish City")
        book.Metadata.publisher_info.set_publish_city("Mars City")
        book.Metadata.publisher_info.set_publish_city(None)
        book.Metadata.publisher_info.set_publish_city("Earth City")


def test_isbn():
    with ACBFBook(edit_dir / "test_isbn.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test ISBN")
        book.Metadata.publisher_info.set_isbn("321-0-98765-432-1")
        book.Metadata.publisher_info.set_isbn(None)
        book.Metadata.publisher_info.set_isbn("123-4-56789-012-3")


def test_license():
    with ACBFBook(edit_dir / "test_license.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test License")
        book.Metadata.publisher_info.set_license("Not real License")
        book.Metadata.publisher_info.set_license(None)
        book.Metadata.publisher_info.set_license("Fictional License")
