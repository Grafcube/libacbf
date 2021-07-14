import os
from pathlib import Path
from libacbf import ACBFBook
from libacbf.structs import Author

edit_dir = Path("tests/results/edit_meta/book_info/")
os.makedirs(edit_dir, exist_ok=True)

def test_authors():
    with ACBFBook(edit_dir / "edit_authors.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Edit Authors")

        book.Metadata.book_info.add_author("Test")
        book.Metadata.book_info.add_author("Hugh", "Mann")
        au = book.Metadata.book_info.authors[-1]
        book.Metadata.book_info.add_author(Author("Grafcube"))
        book.Metadata.book_info.add_author(author=Author("Another", "Grafcube"))
        book.Metadata.book_info.add_author("Remove", "This")
        rem = book.Metadata.book_info.authors[-1]
        book.Metadata.book_info.add_author("NotGrafcube")

        book.Metadata.book_info.edit_author(0, first_name="TheFirst", last_name="TheLast",
                                            middle_name="TheMid", lang="kn", nickname=None,
                                            home_page="https://example.com/testing")

        book.Metadata.book_info.edit_author(au, middle_name=None, lang=None)

        book.Metadata.book_info.edit_author(0, activity="Translator")

        try:
            book.Metadata.book_info.edit_author(au, first_name=None)
        except ValueError as e:
            with open(edit_dir / "author_error.txt", 'w') as op:
                op.write(str(e))

        try:
            book.Metadata.book_info.edit_author(au, something="Non existant")
        except AttributeError as e:
            with open(edit_dir / "no_attribute.txt", 'w') as op:
                op.write(str(e))

        book.Metadata.book_info.remove_author(-1)
        book.Metadata.book_info.remove_author(rem)

def test_titles():
    with ACBFBook(edit_dir / "edit_titles.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Edit Titles")
        book.Metadata.book_info.edit_title("Test Edit Titles", "en")
        book.Metadata.book_info.edit_title("ಹೆಸರು", "kn")
        book.Metadata.book_info.edit_title("ಹೆಸರು ಪರೀಕ್ಷೆ", "kn")
        book.Metadata.book_info.edit_title("タイトル テスト", "jp")
        book.Metadata.book_info.remove_title("jp")
        book.Metadata.book_info.remove_title()

def test_genres():
    with ACBFBook(edit_dir / "edit_genres.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Edit Genres")

        book.Metadata.book_info.edit_genre("other")
        book.Metadata.book_info.edit_genre("non_fiction", 42)
        book.Metadata.book_info.edit_genre("manga", 11)
        book.Metadata.book_info.edit_genre("manga", None)
        book.Metadata.book_info.remove_genre("manga")

def test_annotations():
    with ACBFBook(edit_dir / "edit_annotations.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Edit Annotations")

        book.Metadata.book_info.edit_annotation("This is an annotation.")
        book.Metadata.book_info.edit_annotation("This is an annotation.\nThis is another line.")
        book.Metadata.book_info.edit_annotation("This is an annotation.", "en")
        book.Metadata.book_info.edit_annotation("This is an annotation.\nThis is another line.",
                                                "en")
        book.Metadata.book_info.edit_annotation("ಇದು ಈ ಪುಸ್ತಕದ ವಿವರಣೆ", "kn")
        book.Metadata.book_info.edit_annotation("ಇದು ಈ ಪುಸ್ತಕದ ವಿವರಣೆ.\nಇದು ಎರಡನೇ ಸಾಲು.", "kn")
        book.Metadata.book_info.remove_annotation()
        book.Metadata.book_info.remove_annotation("kn")

# def test_cover page():
# 	pass

# --- Optional ---

def test_languagelayers():
    with ACBFBook(edit_dir / "edit_languages.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Edit Languages")

        book.Metadata.book_info.add_language("en", False)
        book.Metadata.book_info.add_language("en", True)
        en = book.Metadata.book_info.languages[-1]
        book.Metadata.book_info.add_language("kn", False)
        kn = book.Metadata.book_info.languages[-1]
        book.Metadata.book_info.add_language("jp", True)
        book.Metadata.book_info.edit_language(kn, show=True)
        book.Metadata.book_info.edit_language(-1, lang="ta")
        book.Metadata.book_info.remove_language(-1)
        book.Metadata.book_info.remove_language(en)

def test_characters():
    with ACBFBook(edit_dir / "edit_characters.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Edit Characters")

        book.Metadata.book_info.add_character("Test")
        book.Metadata.book_info.add_character("Testing")
        book.Metadata.book_info.add_character("Another")
        book.Metadata.book_info.add_character("And Another")
        book.Metadata.book_info.remove_character("Testing")
        book.Metadata.book_info.remove_character(-1)

# def test_keywords():
# 	op = {}
# 	op["original"] = book.Metadata.book_info.keywords

# 	new_kws = book.Metadata.book_info.keywords["_"].copy()
# 	book.Metadata.book_info.add_keyword(book, *new_kws, lang="en")
# 	op["added"] = book.Metadata.book_info.keywords

# 	book.Metadata.book_info.add_keyword(book, "ebook", "tag", "comic book", "Tag", "TAG", lang="en")
# 	op["updated"] = book.Metadata.book_info.keywords

# 	book.Metadata.book_info.remove_keyword(book, "comic book", "science fiction", "TaG", lang="en")
# 	op["removed"] = book.Metadata.book_info.keywords

# 	book.Metadata.book_info.clear_keywords(book, "en")
# 	op["cleared"] = book.Metadata.book_info.keywords

# 	with open(dir + "test_keywords.json", 'w', encoding="utf-8", newline='\n') as result:
# 		result.write(json.dumps(op, default=list, ensure_ascii=False))

# def test_series():
# 	op = {}
# 	op["original"] = [x.__dict__ for x in book.Metadata.book_info.series.values()]

# 	try:
# 		book.Metadata.book_info.edit_series(book, "Some Comics")
# 	except AttributeError as e:
# 		op["empty-sequence"] = {str(e): [x.__dict__ for x in book.Metadata.book_info.series.values()]}

# 	book.Metadata.book_info.edit_series(book, "Some Comics", 2)
# 	op["added"] = [x.__dict__ for x in book.Metadata.book_info.series.values()]

# 	book.Metadata.book_info.edit_series(book, "Some Comics", volume=1)
# 	op["edited"] = [x.__dict__ for x in book.Metadata.book_info.series.values()]

# 	book.Metadata.book_info.edit_series(book, "Some Comics", volume=None)
# 	op["modified"] = [x.__dict__ for x in book.Metadata.book_info.series.values()]

# 	book.Metadata.book_info.remove_series(book, "Some Comics")
# 	op["removed"] = [x.__dict__ for x in book.Metadata.book_info.series.values()]

# 	with open(dir + "test_series.json", 'w', encoding="utf-8", newline='\n') as result:
# 		result.write(json.dumps(op, ensure_ascii=False))

# def test_rating():
# 	op = {}
# 	op["original"] = book.Metadata.book_info.content_rating

# 	book.Metadata.book_info.edit_content_rating(book, "16+", "Age Rating")
# 	op["added"] = book.Metadata.book_info.content_rating

# 	book.Metadata.book_info.edit_content_rating(book, "17+", "Age Rating")
# 	op["edited"] = book.Metadata.book_info.content_rating

# 	book.Metadata.book_info.remove_content_rating(book, "Age Rating")
# 	op["removed"] = book.Metadata.book_info.content_rating

# 	with open(dir + "test_rating.json", 'w', encoding="utf-8", newline='\n') as result:
# 		result.write(json.dumps(op, ensure_ascii=False))

# def test_dbref():
# 	op = {}
# 	op["original"] = [x.__dict__ for x in book.Metadata.book_info.database_ref]

# 	book.Metadata.book_info.add_database_ref(book, "ComicSite", "123456")
# 	op["added"] = [x.__dict__ for x in book.Metadata.book_info.database_ref]

# 	book.Metadata.book_info.edit_database_ref(book, -1, type="id")
# 	op["edited"] = [x.__dict__ for x in book.Metadata.book_info.database_ref]

# 	book.Metadata.book_info.edit_database_ref(book, -1, ref="https://example.com/comicsite/id/123456", type="URL")
# 	op["modified"] = [x.__dict__ for x in book.Metadata.book_info.database_ref]

# 	book.Metadata.book_info.edit_database_ref(book, -1, type=None)
# 	op["updated"] = [x.__dict__ for x in book.Metadata.book_info.database_ref]

# 	book.Metadata.book_info.remove_database_ref(book, -1)
# 	op["removed"] = [x.__dict__ for x in book.Metadata.book_info.database_ref]

# 	with open(dir + "test_dbref.json", 'w', encoding="utf-8", newline='\n') as result:
# 		result.write(json.dumps(op, default=lambda x : str(x), ensure_ascii=False))
