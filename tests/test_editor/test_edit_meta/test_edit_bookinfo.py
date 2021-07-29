import os
import pytest
from pathlib import Path
from libacbf import ACBFBook
from libacbf.metadata import Author

edit_dir = Path("tests/results/edit_meta/book_info/")
os.makedirs(edit_dir, exist_ok=True)


def test_authors():
    with ACBFBook(edit_dir / "edit_authors.acbf", 'w', archive_type=None) as book:
        book.book_info.edit_title("Test Edit Authors")

        book.book_info.add_author("Test")
        book.book_info.add_author("Hugh", "Mann")
        au = book.book_info.authors[-1]
        book.book_info.add_author(Author("Grafcube"))
        book.book_info.add_author(author=Author("Another", "Grafcube"))
        book.book_info.add_author("Remove", "This")
        rem = book.book_info.authors[-1]
        book.book_info.add_author("NotGrafcube")

        book.book_info.edit_author(0, first_name="TheFirst", last_name="TheLast", middle_name="TheMid",
                                            lang="kn", nickname=None, home_page="https://example.com/testing")

        book.book_info.edit_author(au, middle_name=None, lang=None)

        book.book_info.edit_author(0, activity="Translator")

        try:
            book.book_info.edit_author(au, first_name=None)
        except ValueError as e:
            if str(e) == "Author must have either First Name and Last Name or Nickname.":
                pass
            else:
                raise e

        try:
            book.book_info.edit_author(au, something="Non existant")
        except AttributeError as e:
            if str(e) == "`Author` has no attribute `something`.":
                pass
            else:
                raise e

        book.book_info.remove_author(-1)
        book.book_info.remove_author(rem)


def test_titles():
    with ACBFBook(edit_dir / "edit_titles.acbf", 'w', archive_type=None) as book:
        book.book_info.edit_title("Test Edit Titles")
        book.book_info.edit_title("Test Edit Titles", "en")
        book.book_info.edit_title("ಹೆಸರು", "kn")
        book.book_info.edit_title("ಹೆಸರು ಪರೀಕ್ಷೆ", "kn")
        book.book_info.edit_title("タイトル テスト", "jp")
        book.book_info.remove_title("jp")
        book.book_info.remove_title()


def test_genres():
    with ACBFBook(edit_dir / "edit_genres.acbf", 'w', archive_type=None) as book:
        book.book_info.edit_title("Test Edit Genres")

        book.book_info.edit_genre("other")
        book.book_info.edit_genre("non_fiction", 42)
        book.book_info.edit_genre("manga", 11)
        book.book_info.edit_genre("manga", None)
        book.book_info.remove_genre("manga")


def test_annotations():
    with ACBFBook(edit_dir / "edit_annotations.acbf", 'w', archive_type=None) as book:
        book.book_info.edit_title("Test Edit Annotations")

        book.book_info.edit_annotation("This is an annotation.")
        book.book_info.edit_annotation("This is an annotation.\nThis is another line.")
        book.book_info.edit_annotation("This is an annotation.", "en")
        book.book_info.edit_annotation("This is an annotation.\nThis is another line.", "en")
        book.book_info.edit_annotation("ಇದು ಈ ಪುಸ್ತಕದ ವಿವರಣೆ", "kn")
        book.book_info.edit_annotation("ಇದು ಈ ಪುಸ್ತಕದ ವಿವರಣೆ.\nಇದು ಎರಡನೇ ಸಾಲು.", "kn")
        book.book_info.remove_annotation()
        book.book_info.remove_annotation("kn")


def test_coverpage():
    with ACBFBook(edit_dir / "edit_coverpage.acbf", 'w', archive_type=None) as book:
        book.book_info.edit_title("Test Edit Coverpage Fails")

        with pytest.raises(AttributeError, match=r'`coverpage` has no attribute `\w+`\.'):
            book.book_info.cover_page.set_bgcolor("#ffffff")
            book.book_info.cover_page.set_transition("fade")
            book.book_info.cover_page.set_title("Cover title")


# --- Optional ---

def test_languagelayers():
    with ACBFBook(edit_dir / "edit_languages.acbf", 'w', archive_type=None) as book:
        book.book_info.edit_title("Test Edit Languages")

        book.book_info.add_language("en", False)
        book.book_info.add_language("en", True)
        en = book.book_info.languages[-1]
        book.book_info.add_language("kn", False)
        kn = book.book_info.languages[-1]
        book.book_info.add_language("jp", True)
        book.book_info.edit_language(kn, show=True)
        book.book_info.edit_language(-1, lang="ta")
        book.book_info.remove_language(-1)
        book.book_info.remove_language(en)


def test_characters():
    with ACBFBook(edit_dir / "edit_characters.acbf", 'w', archive_type=None) as book:
        book.book_info.edit_title("Test Edit Characters")

        book.book_info.add_character("Test")
        book.book_info.add_character("Testing")
        book.book_info.add_character("Another")
        book.book_info.add_character("And Another")
        book.book_info.remove_character("Testing")
        book.book_info.remove_character(-1)


def test_keywords():
    with ACBFBook(edit_dir / "edit_keywords.acbf", 'w', archive_type=None) as book:
        book.book_info.edit_title("Test Edit Keywords")

        book.book_info.add_keywords("ebook", "tag", "comic book", "Tag", "TAG")
        book.book_info.add_keywords("ebook", "tag", "comic book", "Tag", "TAG", lang="en")
        book.book_info.remove_keyword("science fiction", "TaG", lang="en")
        book.book_info.clear_keywords()


def test_series():
    with ACBFBook(edit_dir / "edit_series.acbf", 'w', archive_type=None) as book:
        book.book_info.edit_title("Test Edit Series")

        try:
            book.book_info.edit_series("Some Comics")
        except AttributeError as e:
            if str(e) == "`sequence` cannot be blank for new series entry `Some Comics`.":
                pass
            else:
                raise e

        book.book_info.edit_series("Some Comics", 2)
        book.book_info.edit_series("More Comics", 5)
        book.book_info.edit_series("No Comics", 0)
        book.book_info.edit_series("Some Comics", volume=1)
        book.book_info.edit_series("More Comics", volume=2)
        book.book_info.edit_series("Some Comics", volume=None)
        book.book_info.remove_series("No Comics")


def test_rating():
    with ACBFBook(edit_dir / "edit_rating.acbf", 'w', archive_type=None) as book:
        book.book_info.edit_title("Test Edit Content Rating")

        book.book_info.edit_content_rating("16+")
        book.book_info.edit_content_rating("16+", "Age Rating")
        book.book_info.edit_content_rating("16+", "Another Age Rating")
        book.book_info.edit_content_rating("16+", "No Age Rating")
        book.book_info.edit_content_rating("17+", "Another Age Rating")
        book.book_info.remove_content_rating()
        book.book_info.remove_content_rating("No Age Rating")


def test_dbref():
    with ACBFBook(edit_dir / "edit_dbref.acbf", 'w', archive_type=None) as book:
        book.book_info.edit_title("Test Edit Database Reference")

        book.book_info.add_database_ref("ComicSite", "123456")
        cs = book.book_info.database_ref[-1]
        book.book_info.add_database_ref("ComicSite", "123456")
        csu = book.book_info.database_ref[-1]
        book.book_info.add_database_ref("AnotherSite", "654321", "id")
        an = book.book_info.database_ref[-1]
        book.book_info.add_database_ref("NoSite", "654321")
        ns = book.book_info.database_ref[-1]
        book.book_info.add_database_ref("NoSite", "id/654321")
        book.book_info.edit_database_ref(cs, type="id")
        book.book_info.edit_database_ref(csu, ref="https://example.com/comicsite/id/123456", type="URL")
        book.book_info.edit_database_ref(an, type=None)
        book.book_info.remove_database_ref(-1)
        book.book_info.remove_database_ref(ns)
