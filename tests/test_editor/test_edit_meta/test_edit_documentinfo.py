import pytest
from libacbf import ACBFBook


def test_authors(results_edit_documentinfo):
    with ACBFBook(results_edit_documentinfo / "edit_authors.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Edit Authors"

        book.document_info.add_author("Test")
        book.document_info.add_author("Hugh", "Mann")
        au = book.document_info.authors[-1]
        book.document_info.add_author("REMOVE", "ME")
        rem = book.document_info.authors[-1]
        book.document_info.add_author("NotGrafcube")
        book.document_info.add_author("EDIT_ME")
        edit_me = book.document_info.authors[-1]

        match_message = "Author must have either First Name and Last Name or Nickname."
        with pytest.raises(ValueError, match=match_message):
            au.first_name = None
        with pytest.raises(ValueError, match=match_message):
            au.last_name = None
        with pytest.raises(ValueError, match=match_message):
            edit_me.nickname = None

        edit_me.first_name = "TheFirst"
        edit_me.last_name = "TheLast"
        edit_me.nickname = None
        edit_me.middle_name = "TheMid"
        edit_me.home_page = "https://example.com/authors/someone"
        edit_me.email = "someone123@example.com"
        edit_me.lang = "en"
        edit_me.activity = "Translator"
        au.nickname = "NotAPlatypus"

        book.document_info.authors.remove(rem)

        book.create_placeholders()


def test_creation_date(results_edit_documentinfo):
    with ACBFBook(results_edit_documentinfo / "test_creation_date.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Creation Date"
        book.document_info.set_date("3rd Jan, 2021")

        book.create_placeholders()


def test_creation_date_excl(results_edit_documentinfo):
    with ACBFBook(results_edit_documentinfo / "test_creation_date_excl.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Creation Date No ISO"
        book.document_info.set_date("4th Jan, 2021", include_date=False)

        book.create_placeholders()


def test_source(results_edit_documentinfo):
    with ACBFBook(results_edit_documentinfo / "test_source.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Source"
        book.document_info.source = "This is a source.\nThis is another line."

        book.create_placeholders()


def test_id(results_edit_documentinfo):
    with ACBFBook(results_edit_documentinfo / "test_id.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test ID"
        book.document_info.document_id = "123456"

        book.create_placeholders()


def test_version(results_edit_documentinfo):
    with ACBFBook(results_edit_documentinfo / "test_version.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Version"
        book.document_info.document_version = "1.0"

        book.create_placeholders()


def test_history(results_edit_documentinfo):
    with ACBFBook(results_edit_documentinfo / "test_history.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test History"

        book.document_info.document_history.append("v1.0.0: Created history")
        book.document_info.document_history.append("v1.0.1: Added history")
        book.document_info.document_history.append("vAAAAA: REMOVE ME")
        book.document_info.document_history.append("v1.0.2: More history")
        book.document_info.document_history.append("v1.1.0: Finished")

        book.document_info.document_history.pop(2)

        book.create_placeholders()
