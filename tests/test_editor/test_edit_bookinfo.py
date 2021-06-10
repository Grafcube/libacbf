from libacbf.structs import Author
from libacbf.constants import Genres
import os
import json
from pathlib import Path
from tests.conftest import book, sample_path, get_au_op
from libacbf.editor import metadata as edit_meta

dir = f"tests/results/{Path(sample_path).name}/editor/metadata/book_info/"
os.makedirs(dir, exist_ok=True)

def test_authors():
	op = {"original": []}
	for i in book.Metadata.book_info.authors:
		op["original"].append(get_au_op(i))
	with open(dir + "test_authors.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_meta.bookinfo.authors.add(book, Author("Test"))
	op["added"] = []
	for i in book.Metadata.book_info.authors:
		op["added"].append(get_au_op(i))
	with open(dir + "test_authors.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))

	edit_meta.bookinfo.authors.edit(book, -1, first_name="TheFirst", last_name="TheLast", middle_name="TheMid", nickname=None, home_page="https://example.com/testing")
	op["edited"] = []
	for i in book.Metadata.book_info.authors:
		op["edited"].append(get_au_op(i))
	with open(dir + "test_authors.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))

	edit_meta.bookinfo.authors.remove(book, -1)
	op["removed"] = []
	for i in book.Metadata.book_info.authors:
		op["removed"].append(get_au_op(i))
	with open(dir + "test_authors.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))

def test_titles():
	op = {}
	op["original"] = book.Metadata.book_info.book_title
	with open(dir + "test_titles.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_meta.bookinfo.title.edit(book, "ಕ್ರ್ಯಾಪ್ಹೌಂಡ್", "kn")
	op["added"] = book.Metadata.book_info.book_title
	with open(dir + "test_titles.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_meta.bookinfo.title.edit(book, "ಹೆಸರು", "kn")
	op["edited"] = book.Metadata.book_info.book_title
	with open(dir + "test_titles.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_meta.bookinfo.title.remove(book, "kn")
	op["removed"] = book.Metadata.book_info.book_title
	with open(dir + "test_titles.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_genres():
	op = {}
	op["original"] = {x.Genre.name: x.Match for x in book.Metadata.book_info.genres.values()}
	with open(dir + "test_genres.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_meta.bookinfo.genres.edit(book, Genres.other)
	op["added"] = {x.Genre.name: x.Match for x in book.Metadata.book_info.genres.values()}
	with open(dir + "test_genres.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_meta.bookinfo.genres.edit(book, Genres.other, 42)
	op["edited"] = {x.Genre.name: x.Match for x in book.Metadata.book_info.genres.values()}
	with open(dir + "test_genres.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_meta.bookinfo.genres.remove(book, Genres.other)
	op["removed"] = {x.Genre.name: x.Match for x in book.Metadata.book_info.genres.values()}
	with open(dir + "test_genres.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_annotations():
	op = {}
	op["original"] = book.Metadata.book_info.annotations
	with open(dir + "test_annotations.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_meta.bookinfo.annotation.edit(book, "ಇದು ಈ ಪುಸ್ತಕದ ವಿವರಣೆ", "kn")
	op["added"] = book.Metadata.book_info.annotations
	with open(dir + "test_annotations.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_meta.bookinfo.annotation.edit(book, "ಇದು ಈ ಪುಸ್ತಕದ ವಿವರಣೆ.\nಇದು ಎರಡನೇ ಸಾಲು.", "kn")
	op["edited"] = book.Metadata.book_info.annotations
	with open(dir + "test_annotations.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_meta.bookinfo.annotation.remove(book, "kn")
	op["removed"] = book.Metadata.book_info.annotations
	with open(dir + "test_annotations.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_coverpage():
	pass

def test_languagelayers():
	op = {}
	op["original"] = [{"lang": x.lang, "show": x.show} for x in book.Metadata.book_info.languages]
	with open(dir + "test_languages.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_meta.bookinfo.languagelayers.add(book, "kn", False)
	op["added"] = [{"lang": x.lang, "show": x.show} for x in book.Metadata.book_info.languages]
	with open(dir + "test_languages.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_meta.bookinfo.languagelayers.edit(book, -1, show=True)
	op["edited"] = [{"lang": x.lang, "show": x.show} for x in book.Metadata.book_info.languages]
	with open(dir + "test_languages.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_meta.bookinfo.languagelayers.edit(book, -1, lang="ta")
	op["edited_again"] = [{"lang": x.lang, "show": x.show} for x in book.Metadata.book_info.languages]
	with open(dir + "test_languages.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

	edit_meta.bookinfo.languagelayers.remove(book, -1)
	op["removed"] = [{"lang": x.lang, "show": x.show} for x in book.Metadata.book_info.languages]
	with open(dir + "test_languages.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))
