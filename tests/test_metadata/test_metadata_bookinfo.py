import os
import json
from pathlib import Path
from typing import Dict
from tests.conftest import get_au_op
from libacbf import ACBFBook

def make_bookinfo_dir(path):
	os.makedirs(path/"metadata/book_info/", exist_ok=True)
	return path/"metadata/book_info/"

def test_authors(read_books: Dict[Path, ACBFBook]):
	for path, book in read_books.items():
		dir = make_bookinfo_dir(path)
		op = []
		for i in book.Metadata.book_info.authors:
			op.append(get_au_op(i))
		print(op)
		with open(dir/"test_bookinfo_authors.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))

def test_titles(read_books: Dict[Path, ACBFBook]):
	for path, book in read_books.items():
		dir = make_bookinfo_dir(path)
		op = book.Metadata.book_info.book_title
		print(op)
		with open(dir/"test_bookinfo_titles.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))

def test_genres(read_books: Dict[Path, ACBFBook]):
	for path, book in read_books.items():
		dir = make_bookinfo_dir(path)
		op = {}
		for i in book.Metadata.book_info.genres.keys():
			op[book.Metadata.book_info.genres[i].Genre.name] = book.Metadata.book_info.genres[i].Match
		print(op)
		with open(dir/"test_bookinfo_genres.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))

def test_annotations(read_books: Dict[Path, ACBFBook]):
	for path, book in read_books.items():
		dir = make_bookinfo_dir(path)
		op = book.Metadata.book_info.annotations
		print(op)
		with open(dir/"test_bookinfo_annotations.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))

def test_languages(read_books: Dict[Path, ACBFBook]):
	for path, book in read_books.items():
		dir = make_bookinfo_dir(path)
		op = []
		for i in book.Metadata.book_info.languages:
			new_op = {
				"lang": i.lang,
				"show": i.show
			}
			op.append(new_op)
		print(op)
		with open(dir/"test_bookinfo_languages.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))

def test_characters(read_books: Dict[Path, ACBFBook]):
	for path, book in read_books.items():
		dir = make_bookinfo_dir(path)
		print(book.Metadata.book_info.characters)
		with open(dir/"test_bookinfo_characters.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(book.Metadata.book_info.characters, ensure_ascii=False))

def test_keywords(read_books: Dict[Path, ACBFBook]):
	for path, book in read_books.items():
		dir = make_bookinfo_dir(path)
		op = book.Metadata.book_info.keywords
		print(op)
		with open(dir/"test_bookinfo_keywords.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, default=list, ensure_ascii=False))

def test_series(read_books: Dict[Path, ACBFBook]):
	for path, book in read_books.items():
		dir = make_bookinfo_dir(path)
		op = {}
		for i in book.Metadata.book_info.series.keys():
			op[i] = {
				"title": book.Metadata.book_info.series[i].title,
				"sequence": book.Metadata.book_info.series[i].sequence,
				"volume": book.Metadata.book_info.series[i].volume
			}
		print(op)
		with open(dir/"test_bookinfo_series.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))

def test_content_rating(read_books: Dict[Path, ACBFBook]):
	for path, book in read_books.items():
		dir = make_bookinfo_dir(path)
		print(book.Metadata.book_info.content_rating)
		with open(dir/"test_bookinfo_content_rating.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(book.Metadata.book_info.content_rating, ensure_ascii=False))

def test_database_ref(read_books: Dict[Path, ACBFBook]):
	for path, book in read_books.items():
		dir = make_bookinfo_dir(path)
		op = []
		for i in book.Metadata.book_info.database_ref:
			new_op = {
				"dbname": i.dbname,
				"text": i.reference,
				"type": i.type
			}
			op.append(new_op)
		print(op)
		with open(dir/"test_bookinfo_database_ref.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))

def test_coverpage(read_books: Dict[Path, ACBFBook]):
	for path, book in read_books.items():
		dir = make_bookinfo_dir(path)
		op = {
			"image_ref": book.Metadata.book_info.cover_page.image_ref,
			"image_name": book.Metadata.book_info.cover_page.image.id,
			"image_size": len(book.Metadata.book_info.cover_page.image.data),
			"text_layers": None,
			"frames": None,
			"jumps": None
		}
		op_tlayers = {}
		for i in book.Metadata.book_info.cover_page.text_layers.keys():
			op_tlayers[i] = {
				"language": book.Metadata.book_info.cover_page.text_layers[i].language,
				"bg_color": book.Metadata.book_info.cover_page.text_layers[i].bgcolor,
				"text_areas": None
			}
			op_tareas = []
			for j in book.Metadata.book_info.cover_page.text_layers[i].text_areas:
				new_tarea = {
					"points": j.points,
					"paragraph": j.paragraph,
					"bg_color": j.bgcolor,
					"rotation": j.rotation,
					"type": j.type,
					"inverted": j.inverted,
					"transparent": j.transparent
				}
				op_tareas.append(new_tarea)
			op_tlayers[i]["text_areas"] = op_tareas
		op["text_layers"] = op_tlayers
		op_frames = []
		for i in book.Metadata.book_info.cover_page.frames:
			new_fr = {
				"points": i.points,
				"bgcolor": i.bgcolor
			}
			op_frames.append(new_fr)
		op["frames"] = op_frames
		op_jumps = []
		for i in book.Metadata.book_info.cover_page.jumps:
			new_jm = {
				"page": i.page,
				"points": i.points
			}
			op_jumps.append(new_jm)
		op["jumps"] = op_jumps
		print(op)
		with open(dir/"test_bookinfo_cover_page.json", 'w', encoding="utf-8", newline='\n') as result:
			result.write(json.dumps(op, ensure_ascii=False))
