import os
from pathlib import Path
from libacbf import ACBFBook
from libacbf.metadata import Author

edit_dir = Path("tests/results/edit_meta/document_info/")
os.makedirs(edit_dir, exist_ok=True)


def test_authors():
    with ACBFBook(edit_dir / "edit_authors.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Edit Authors")

        book.Metadata.document_info.add_author("Test")
        book.Metadata.document_info.add_author("Hugh", "Mann")
        au = book.Metadata.document_info.authors[-1]
        book.Metadata.document_info.add_author(Author("Grafcube"))
        book.Metadata.document_info.add_author(author=Author("Another", "Grafcube"))
        book.Metadata.document_info.add_author("Remove", "This")
        rem = book.Metadata.document_info.authors[-1]
        book.Metadata.document_info.add_author("NotGrafcube")

        book.Metadata.document_info.edit_author(0, first_name="TheFirst", last_name="TheLast", middle_name="TheMid",
                                                lang="kn", nickname=None, home_page="https://example.com/testing")

        book.Metadata.document_info.edit_author(au, middle_name=None, lang=None)

        book.Metadata.document_info.edit_author(0, activity="Translator")

        try:
            book.Metadata.document_info.edit_author(au, first_name=None)
        except ValueError as e:
            if str(e) == "Author must have either First Name and Last Name or Nickname.":
                pass
            else:
                raise e

        try:
            book.Metadata.document_info.edit_author(au, something="Non existant")
        except AttributeError as e:
            if str(e) == "`Author` has no attribute `something`.":
                pass
            else:
                raise e

        book.Metadata.document_info.remove_author(-1)
        book.Metadata.document_info.remove_author(rem)


def test_creation_date():
    with ACBFBook(edit_dir / "test_creation_date.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Creation Date")
        book.Metadata.document_info.set_creation_date("3rd Jan, 2021")


def test_creation_date_excl():
    with ACBFBook(edit_dir / "test_creation_date_excl.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Creation Date No ISO")
        book.Metadata.document_info.set_creation_date("4th Jan, 2021", include_date=False)


def test_source():
    with ACBFBook(edit_dir / "test_source.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Source")

        book.Metadata.document_info.set_source("This is a source.")
        book.Metadata.document_info.set_source(None)
        book.Metadata.document_info.set_source("This is another source.")
        book.Metadata.document_info.set_source("This is a source.\nThis is another line.")


def test_id():
    with ACBFBook(edit_dir / "test_id.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test ID")

        book.Metadata.document_info.set_document_id("654321")
        book.Metadata.document_info.set_document_id(None)
        book.Metadata.document_info.set_document_id("123456")


def test_version():
    with ACBFBook(edit_dir / "test_version.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Version")

        book.Metadata.document_info.set_document_version(1.0)
        book.Metadata.document_info.set_document_version(None)
        book.Metadata.document_info.set_document_version(1.1)


def test_history():
    with ACBFBook(edit_dir / "test_history.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test History")

        book.Metadata.document_info.append_history("v1.0.0: Created history")
        book.Metadata.document_info.append_history("v1.0.1: Added history")
        book.Metadata.document_info.append_history("vAAAAA: REMOVE ME")
        book.Metadata.document_info.append_history("v1.0.3: More history")
        book.Metadata.document_info.append_history("v1.0.0: EDIT ME")
        book.Metadata.document_info.append_history("v1.0.5: Even more history")
        book.Metadata.document_info.append_history("v1.1.0: Finished")

        book.Metadata.document_info.remove_history(2)
        book.Metadata.document_info.insert_history(2, "v1.0.2: Inserted history")
        book.Metadata.document_info.edit_history(4, "v1.0.4: Edited history")
