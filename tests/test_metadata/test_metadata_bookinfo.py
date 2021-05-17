import os
import json
from pathlib import Path
from langcodes import Language
from tests.conftest import book, sample_path

dir = f"tests/results/{Path(sample_path).name}/metadata/book_info/"
os.makedirs(dir, exist_ok=True)

def test_authors():
	op = []
	for i in book.Metadata.book_info.authors:
		new_op = {
			"activity": i.activity.name,
			"lang": i.lang if i.lang is not None else None,
			"first_name": i.first_name,
			"last_name": i.last_name,
			"middle_name": i.middle_name,
			"nickname": i.nickname,
			"home_page": i.home_page,
			"email": i.email
		}
		op.append(new_op)
	print(op)
	with open(dir + "test_bookinfo_authors.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_titles():
	op = book.Metadata.book_info.book_title
	print(op)
	with open(dir + "test_bookinfo_titles.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_genres():
	op = {}
	for i in book.Metadata.book_info.genres.keys():
		op[book.Metadata.book_info.genres[i].Genre.name] = book.Metadata.book_info.genres[i].Match
	print(op)
	with open(dir + "test_bookinfo_genres.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_annotations():
	op = book.Metadata.book_info.annotations
	print(op)
	with open(dir + "test_bookinfo_annotations.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_languages():
	op = []
	for i in book.Metadata.book_info.languages:
		new_op = {
			"lang": i.lang,
			"show": i.show
		}
		op.append(new_op)
	print(op)
	with open(dir + "test_bookinfo_languages.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_characters():
	print(book.Metadata.book_info.characters)
	with open(dir + "test_bookinfo_characters.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(book.Metadata.book_info.characters, ensure_ascii=False))

def test_keywords():
	op = book.Metadata.book_info.keywords
	print(op)
	with open(dir + "test_bookinfo_keywords.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_series():
	op = {}
	for i in book.Metadata.book_info.series.keys():
		op[i] = {
			"title": book.Metadata.book_info.series[i].title,
			"sequence": book.Metadata.book_info.series[i].sequence,
			"volume": book.Metadata.book_info.series[i].volume
		}
	print(op)
	with open(dir + "test_bookinfo_series.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_content_rating():
	print(book.Metadata.book_info.content_rating)
	with open(dir + "test_bookinfo_content_rating.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(book.Metadata.book_info.content_rating, ensure_ascii=False))

def test_database_ref():
	op = []
	for i in book.Metadata.book_info.database_ref:
		new_op = {
			"dbname": i.dbname,
			"text": i.reference,
			"type": i.type
		}
		op.append(new_op)
	print(op)
	with open(dir + "test_bookinfo_database_ref.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_coverpage():
	op = {
		"image_ref": book.Metadata.book_info.cover_page.image_ref,
		"image_name": book.Metadata.book_info.cover_page.image.id,
		"image_size": book.Metadata.book_info.cover_page.image.filesize,
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
	with open(dir + "test_bookinfo_cover_page.json", 'w', encoding="utf-8", newline='\n') as result:
		result.write(json.dumps(op, ensure_ascii=False))
