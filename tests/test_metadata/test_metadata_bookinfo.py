import json
from langcodes import Language
from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.ACBFBook import ACBFBook
from tests.testsettings import sample_path

book = ACBFBook(sample_path)
book.close()
book_metadata: ACBFMetadata = book.Metadata

def test_authors():
	op = []
	for i in book_metadata.book_info.authors:
		new_op = {
			"activity": i.activity.name,
			"lang": str(i.lang) if i.lang is not None else None,
			"first_name": i.first_name,
			"last_name": i.last_name,
			"middle_name": i.middle_name,
			"nickname": i.nickname,
			"home_page": i.home_page,
			"email": i.email
		}
		op.append(new_op)
	print(op)
	with open("tests/results/metadata/book_info/test_bookinfo_authors.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_titles():
	op = {}
	for i in book_metadata.book_info.book_title.keys():
		key = str(i) if type(i) is Language else i
		op[key] = book_metadata.book_info.book_title[i]
	print(op)
	with open("tests/results/metadata/book_info/test_bookinfo_titles.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_genres():
	op = {}
	for i in book_metadata.book_info.genres.keys():
		op[book_metadata.book_info.genres[i].Genre.name] = book_metadata.book_info.genres[i].Match
	print(op)
	with open("tests/results/metadata/book_info/test_bookinfo_genres.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_annotations():
	op = {}
	for i in book_metadata.book_info.annotations.keys():
		key = str(i) if type(i) is Language else i
		op[key] = book_metadata.book_info.annotations[i]
	print(op)
	with open("tests/results/metadata/book_info/test_bookinfo_annotations.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_languages():
	op = []
	for i in book_metadata.book_info.languages:
		new_op = {
			"lang": i.lang,
			"show": i.show
		}
		op.append(new_op)
	print(op)
	with open("tests/results/metadata/book_info/test_bookinfo_languages.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_characters():
	print(book_metadata.book_info.characters)
	with open("tests/results/metadata/book_info/test_bookinfo_characters.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.book_info.characters, ensure_ascii=False))

def test_keywords():
	op = {}
	for i in book_metadata.book_info.keywords.keys():
		key = str(i) if type(i) is Language else i
		op[key] = book_metadata.book_info.keywords[i]
	print(op)
	with open("tests/results/metadata/book_info/test_bookinfo_keywords.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_series():
	op = {}
	for i in book_metadata.book_info.series.keys():
		op[i] = {
			"title": book_metadata.book_info.series[i].title,
			"sequence": book_metadata.book_info.series[i].sequence,
			"lang": book_metadata.book_info.series[i].lang,
			"volume": book_metadata.book_info.series[i].volume
		}
	print(op)
	with open("tests/results/metadata/book_info/test_bookinfo_series.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_content_rating():
	print(book_metadata.book_info.content_rating)
	with open("tests/results/metadata/book_info/test_bookinfo_content_rating.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(book_metadata.book_info.content_rating, ensure_ascii=False))

def test_database_ref():
	op = []
	for i in book_metadata.book_info.database_ref:
		new_op = {
			"dbname": i.dbname,
			"text": i.text,
			"type": i.type
		}
		op.append(new_op)
	print(op)
	with open("tests/results/metadata/book_info/test_bookinfo_database_ref.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(op, ensure_ascii=False))

def test_coverpage():
	op = {
		"image_ref": book_metadata.book_info.cover_page.image_ref,
		"text_layers": None,
		"frames": None,
		"jumps": None
	}
	op_tlayers = {}
	for i in book_metadata.book_info.cover_page.text_layers.keys():
		op_tlayers[i] = {
			"language": book_metadata.book_info.cover_page.text_layers[i].language,
			"bg_color": book_metadata.book_info.cover_page.text_layers[i].bg_color,
			"text_areas": None
		}
		op_tareas = []
		for j in book_metadata.book_info.cover_page.text_layers[i].text_areas:
			new_tarea = {
				"points": j.points,
				"paragraph": j.paragraph,
				"bg_color": j.bg_color,
				"rotation": j.rotation,
				"type": j.type,
				"inverted": j.inverted,
				"transparent": j.transparent
			}
			op_tareas.append(new_tarea)
		op_tlayers[i]["text_areas"] = op_tareas
	op["text_layers"] = op_tlayers
	op_frames = []
	for i in book_metadata.book_info.cover_page.frames:
		new_fr = {
			"points": i.points,
			"bgcolor": i.bgcolor
		}
		op_frames.append(new_fr)
	op["frames"] = op_frames
	op_jumps = []
	for i in book_metadata.book_info.cover_page.jumps:
		new_jm = {
			"page": i.page,
			"points": i.points
		}
		op_jumps.append(new_jm)
	op["jumps"] = op_jumps
	print(op)
	with open("tests/results/metadata/book_info/test_bookinfo_cover_page.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(op, ensure_ascii=False))
