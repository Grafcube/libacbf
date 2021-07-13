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

        book.Metadata.book_info.edit_author(0,
                                            first_name="TheFirst",
                                            last_name="TheLast",
                                            middle_name="TheMid",
                                            lang="kn",
                                            nickname=None,
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

# def test_titles():
# 	op = {}
# 	op["original"] = book.Metadata.book_info.book_title

# 	book.Metadata.book_info.edit_title(book, "ಕ್ರ್ಯಾಪ್ಹೌಂಡ್", "kn")
# 	op["added"] = book.Metadata.book_info.book_title

# 	book.Metadata.book_info.edit_title(book, "ಹೆಸರು", "kn")
# 	op["edited"] = book.Metadata.book_info.book_title

# 	book.Metadata.book_info.remove_title(book, "kn")
# 	op["removed"] = book.Metadata.book_info.book_title

# 	with open(dir + "test_titles.json", 'w', encoding="utf-8", newline='\n') as result:
# 		result.write(json.dumps(op, ensure_ascii=False))

# def test_genres():
# 	op = {}
# 	op["original"] = {x.genre.name: x.match for x in book.Metadata.book_info.genres.values()}

# 	book.Metadata.book_info.edit_genre(book, Genres.other)
# 	op["added"] = {x.genre.name: x.match for x in book.Metadata.book_info.genres.values()}

# 	book.Metadata.book_info.edit_genre(book, Genres.other, 42)
# 	op["edited"] = {x.genre.name: x.match for x in book.Metadata.book_info.genres.values()}

# 	book.Metadata.book_info.edit_genre(book, Genres.other, None)
# 	op["modified"] = {x.genre.name: x.match for x in book.Metadata.book_info.genres.values()}

# 	book.Metadata.book_info.remove_genre(book, Genres.other)
# 	op["removed"] = {x.genre.name: x.match for x in book.Metadata.book_info.genres.values()}

# 	with open(dir + "test_genres.json", 'w', encoding="utf-8", newline='\n') as result:
# 		result.write(json.dumps(op, ensure_ascii=False))

# def test_annotations():
# 	op = {}
# 	op["original"] = book.Metadata.book_info.annotations

# 	book.Metadata.book_info.edit_annotation(book, "ಇದು ಈ ಪುಸ್ತಕದ ವಿವರಣೆ", "kn")
# 	op["added"] = book.Metadata.book_info.annotations

# 	book.Metadata.book_info.edit_annotation(book, "ಇದು ಈ ಪುಸ್ತಕದ ವಿವರಣೆ.\nಇದು ಎರಡನೇ ಸಾಲು.", "kn")
# 	op["edited"] = book.Metadata.book_info.annotations

# 	book.Metadata.book_info.remove_annotation(book, "kn")
# 	op["removed"] = book.Metadata.book_info.annotations

# 	with open(dir + "test_annotations.json", 'w', encoding="utf-8", newline='\n') as result:
# 		result.write(json.dumps(op, ensure_ascii=False))

# def test_coverpage():
# 	pass

# def test_languagelayers():
# 	op = {}
# 	op["original"] = [{"lang": x.lang, "show": x.show} for x in book.Metadata.book_info.languages]

# 	book.Metadata.book_info.add_language(book, "kn", False)
# 	op["added"] = [{"lang": x.lang, "show": x.show} for x in book.Metadata.book_info.languages]

# 	book.Metadata.book_info.edit_language(book, -1, show=True)
# 	op["edited"] = [{"lang": x.lang, "show": x.show} for x in book.Metadata.book_info.languages]

# 	book.Metadata.book_info.edit_language(book, -1, lang="ta")
# 	op["edited_again"] = [{"lang": x.lang, "show": x.show} for x in book.Metadata.book_info.languages]

# 	book.Metadata.book_info.remove_language(book, -1)
# 	op["removed"] = [{"lang": x.lang, "show": x.show} for x in book.Metadata.book_info.languages]

# 	with open(dir + "test_languages.json", 'w', encoding="utf-8", newline='\n') as result:
# 		result.write(json.dumps(op, ensure_ascii=False))

# def test_characters():
# 	op = {}
# 	op["original"] = ", ".join(book.Metadata.book_info.characters)

# 	book.Metadata.book_info.add_character(book, "Test")
# 	book.Metadata.book_info.add_character(book, "Another")
# 	op["added"] = ", ".join(book.Metadata.book_info.characters)

# 	book.Metadata.book_info.remove_character(book, "Test")
# 	book.Metadata.book_info.remove_character(book, -1)
# 	op["removed"] = ", ".join(book.Metadata.book_info.characters)

# 	with open(dir + "test_characters.json", 'w', encoding="utf-8", newline='\n') as result:
# 		result.write(json.dumps(op, ensure_ascii=False))

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
