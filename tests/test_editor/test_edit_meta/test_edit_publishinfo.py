from libacbf import ACBFBook


def test_publisher(results_edit_publishinfo):
    with ACBFBook(results_edit_publishinfo / "test_publisher.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Publisher"
        book.publisher_info.publisher = "Grafcube"

        book._create_placeholders()


def test_publish_date(results_edit_publishinfo):
    with ACBFBook(results_edit_publishinfo / "test_publish_date.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Publish Date"
        book.publisher_info.set_date("1st Jan, 2021")

        book._create_placeholders()


def test_publish_date_excl(results_edit_publishinfo):
    with ACBFBook(results_edit_publishinfo / "test_publish_date_excl.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Publish Date No ISO"
        book.publisher_info.set_date("2nd Jan, 2021", include_date=False)

        book._create_placeholders()


def test_city(results_edit_publishinfo):
    with ACBFBook(results_edit_publishinfo / "test_city.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Publish City"
        book.publisher_info.publish_city = "Earth City"

        book._create_placeholders()


def test_isbn(results_edit_publishinfo):
    with ACBFBook(results_edit_publishinfo / "test_isbn.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test ISBN"
        book.publisher_info.isbn = "123-4-56789-012-3"

        book._create_placeholders()


def test_license(results_edit_publishinfo):
    with ACBFBook(results_edit_publishinfo / "test_license.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test License"
        book.publisher_info.license = "Fictional License"

        book._create_placeholders()
