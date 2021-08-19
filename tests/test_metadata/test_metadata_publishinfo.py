import os
from libacbf import ACBFBook
from tests.testres import samples


def test_publisher(results):
    dir = results / "test_metadata/publish_info"
    os.makedirs(dir, exist_ok=True)

    with ACBFBook(samples["cbz"]) as book:
        with open(dir / "test_publisher.txt", 'w', encoding="utf-8", newline='\n') as result:
            result.write(book.publisher_info.publisher)


def test_publish_date_string(results):
    dir = results / "test_metadata/publish_info"
    os.makedirs(dir, exist_ok=True)

    with ACBFBook(samples["cbz"]) as book:
        with open(dir / "test_publish_date_string.txt", 'w', encoding="utf-8", newline='\n') as result:
            result.write(book.publisher_info.publish_date)


def test_publish_date(results):
    dir = results / "test_metadata/publish_info"
    os.makedirs(dir, exist_ok=True)

    with ACBFBook(samples["cbz"]) as book:
        with open(dir / "test_publish_date.txt", 'w', encoding="utf-8", newline='\n') as result:
            result.write(str(book.publisher_info.publish_date_value))


def test_city(results):
    dir = results / "test_metadata/publish_info"
    os.makedirs(dir, exist_ok=True)

    with ACBFBook(samples["cbz"]) as book:
        with open(dir / "test_city.txt", 'w', encoding="utf-8", newline='\n') as result:
            result.write(book.publisher_info.publish_city)


def test_isbn(results):
    dir = results / "test_metadata/publish_info"
    os.makedirs(dir, exist_ok=True)

    with ACBFBook(samples["cbz"]) as book:
        with open(dir / "test_isbn.txt", 'w', encoding="utf-8", newline='\n') as result:
            result.write(book.publisher_info.isbn)


def test_license(results):
    dir = results / "test_metadata/publish_info"
    os.makedirs(dir, exist_ok=True)

    with ACBFBook(samples["cbz"]) as book:
        with open(dir / "test_license.txt", 'w', encoding="utf-8", newline='\n') as result:
            result.write(book.publisher_info.license)
