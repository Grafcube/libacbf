import pytest
from libacbf import ACBFBook


def test_authors(results_bookinfo):
    with ACBFBook(results_bookinfo / "edit_authors.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Edit Authors"

        book.book_info.add_author("Test")
        book.book_info.add_author("Hugh", "Mann")
        au = book.book_info.authors[-1]
        book.book_info.add_author("REMOVE", "ME")
        rem = book.book_info.authors[-1]
        book.book_info.add_author("NotGrafcube")
        book.book_info.add_author("EDIT_ME")
        edit_me = book.book_info.authors[-1]

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

        book.book_info.authors.remove(rem)

        book._create_placeholders()


def test_titles(results_bookinfo):
    with ACBFBook(results_bookinfo / "edit_titles.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Edit Titles"
        book.book_info.book_title["en"] = "Test Edit Titles"
        book.book_info.book_title["kn"] = "ಹೆಸರು ಪರಿಕ್ಷೆ"
        book.book_info.book_title.pop('_')

        book._create_placeholders()


def test_genres(results_bookinfo):
    with ACBFBook(results_bookinfo / "edit_genres.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Edit Genres"

        book.book_info.edit_genre("other")
        book.book_info.edit_genre("horror", 42)
        book.book_info.edit_genre("manga", 11)
        book.book_info.pop_genre("horror")

        assert book.book_info.get_genre_match("manga") == 11

        with pytest.raises(ValueError, match="`match` must be an integer from 0 to 100."):
            book.book_info.edit_genre("other", -1)
        with pytest.raises(ValueError, match="`match` must be an integer from 0 to 100."):
            book.book_info.edit_genre("other", 101)

        book._create_placeholders()


def test_annotations(results_bookinfo):
    with ACBFBook(results_bookinfo / "edit_annotations.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Edit Annotations"

        book.book_info.annotations['_'] = "This is an annotation."
        book.book_info.annotations["en"] = "This is an annotation.\nThis is another line."
        book.book_info.annotations["kn"] = "ಇದು ಈ ಪುಸ್ತಕದ ವಿವರಣೆ.\nಇದು ಎರಡನೇ ಸಾಲು."
        book.book_info.annotations.pop('_')

        book._create_placeholders()


# --- Optional ---

def test_languagelayers(results_bookinfo):
    with ACBFBook(results_bookinfo / "edit_languages.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Edit Languages"

        book.book_info.add_language("en", False)
        book.book_info.add_language("en", False)
        en = book.book_info.languages[-1]
        book.book_info.add_language("kn", False)
        kn = book.book_info.languages[-1]
        book.book_info.add_language("ta", True)
        book.book_info.languages.pop(-1)
        en.show = True
        kn.show = True

        book._create_placeholders()


def test_characters(results_bookinfo):
    with ACBFBook(results_bookinfo / "edit_characters.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Edit Characters"

        book.book_info.characters.extend(["Testing", "REMOVE_ME", "Another", "And Another"])
        book.book_info.characters.remove("REMOVE_ME")

        book._create_placeholders()


def test_keywords(results_bookinfo):
    with ACBFBook(results_bookinfo / "edit_keywords.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Edit Keywords"

        book.book_info.keywords['_'] = {"ebook", "tag", "comic book", "tag"}
        book.book_info.keywords["en"] = {"ebook", "tag", "comic book", "tag"}
        book.book_info.keywords["kn"] = {"ಪುಸ್ತಕ", "ಹೆಸರು", "ಕಾಮಿಕ್ ಪುಸ್ತಕ", "ಹೆಸರು"}
        book.book_info.keywords.pop('_')

        book._create_placeholders()


def test_series(results_bookinfo):
    with ACBFBook(results_bookinfo / "edit_series.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Edit Series"

        book.book_info.add_series("Some Comics", 2)
        book.book_info.add_series("More Comics", 5, 1)
        book.book_info.add_series("Even More Comics", 7, 2)
        book.book_info.add_series("No Comics", 0)
        book.book_info.series["Even More Comics"].volume = None
        book.book_info.series.pop("No Comics")

        book._create_placeholders()


def test_rating(results_bookinfo):
    with ACBFBook(results_bookinfo / "edit_rating.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Edit Content Rating"

        book.book_info.content_rating["Age Rating"] = "16+"
        book.book_info.content_rating["DC Comics rating system"] = "T+"
        book.book_info.content_rating["Marvel Comics rating system"] = "PARENTAL ADVISORY"
        book.book_info.content_rating["REMOVE_ME"] = '0'
        book.book_info.content_rating.pop("REMOVE_ME")

        book._create_placeholders()


def test_dbref(results_bookinfo):
    with ACBFBook(results_bookinfo / "edit_dbref.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Edit Database Reference"

        book.book_info.add_dbref("ComicSite", "123456")
        book.book_info.add_dbref("ComicSite", "123456")
        csu = book.book_info.database_ref[-1]
        book.book_info.add_dbref("NoSite", "000000")
        ns = book.book_info.database_ref[-1]
        book.book_info.add_dbref("AnotherSite", "654321", "ID")

        csu.type = "URL"
        csu.reference = "https://example.com/comicsite/id/123456"

        book.book_info.database_ref.remove(ns)

        book._create_placeholders()
