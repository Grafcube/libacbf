import pytest
from libacbf import ACBFBook
from libacbf.exceptions import EditRARArchiveError


def test_create_acbf(results):
    with ACBFBook(results / "test_create.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Create"
        book.book_info.annotations['_'] = "This was created by a test.\nACBF XML File"
        book._create_placeholders()


def test_create_cbz(results):
    with ACBFBook(results / "test_create.cbz", 'w') as book:
        book.book_info.book_title['_'] = "Test Create"
        book.book_info.annotations['_'] = "This was created by a test.\nZip Archive."
        book._create_placeholders()


def test_create_cb7(results):
    with ACBFBook(results / "test_create.cb7", 'w', archive_type="SevenZip") as book:
        book.book_info.book_title['_'] = "Test Create"
        book.book_info.annotations['_'] = "This was created by a test.\n7Zip Archive."
        book._create_placeholders()


def test_create_cbt(results):
    with ACBFBook(results / "test_create.cbt", 'w', archive_type="Tar") as book:
        book.book_info.book_title['_'] = "Test Create"
        book.book_info.annotations['_'] = "This was created by a test.\nTar Archive."
        book._create_placeholders()


def test_create_cbr(results):
    with pytest.raises(EditRARArchiveError):
        with ACBFBook(results / "test_create.cbr", 'w', archive_type="Rar") as _:
            pass


@pytest.mark.parametrize("ext, type", (("cbz", "Zip"), ("cb7", "SevenZip"), ("cbt", "Tar")))
def test_acbf_to_cbz(ext, type, results_edit_convert):
    with ACBFBook(results_edit_convert / f"test_acbf_to_archive.{ext}", 'w', None) as book:
        book.book_info.book_title['_'] = f"Test Convert to {type}"
        book.make_archive(type)
        book._create_placeholders()
