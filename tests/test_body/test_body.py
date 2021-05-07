import json
from libacbf.ACBFBook import ACBFBook

sample_path = "tests/samples/Doctorow, Cory - Craphound.cb7"
book = ACBFBook(sample_path)
book_body = book.Body

def test_body_info():
	print(book_body.bgcolor)
	print(book_body.total_pages)
	with open("tests/results/body/test_body_info.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps({"bgcolour": book_body.bgcolor, "pages": book_body.total_pages}, ensure_ascii=False))

def test_body_pages():
	page_output = {}
	textlayer_output = {}
	fr_jm_output = {
		"frames": {},
		"jumps": {}
	}
	for pg in list(iter(book_body)):
		transition = pg.transition.name if pg.transition is not None else None
		new_pg = {
			"bgcolour": pg.bg_color,
			"transition": transition,
			"ref_type": pg.ref_type.name,
			"titles": pg.title
		}
		page_output[pg.image_ref] = new_pg

		for fr in pg.frames:
			pts = []
			for p in fr.points:
				pts.append(f"({p.x},{p.y})")

			new_fr = {
				"bgcolor": fr.bgcolor,
				"points": pts
			}
			fr_jm_output["frames"][pg.image_ref] = new_fr

		for jm in pg.jumps:
			pts = []
			for p in jm.points:
				pts.append(f"({p.x},{p.y})")

			new_jm = {
				"page": jm.page,
				"points": pts
			}
			fr_jm_output["jumps"][pg.image_ref] = new_jm

		for tl in pg.text_layers.keys():
			new_tl = {
				"lang": str(pg.text_layers[tl].language),
				"bgcolour": pg.text_layers[tl].bg_color,
				"text_areas": []
			}
			for ta in pg.text_layers[tl].text_areas:
				pts = []
				for p in ta.points:
					pts.append(f"({p.x},{p.y})")

				type = ta.type.name if ta.type is not None else None
				new_ta = {
					"points": pts,
					"p": ta.paragraph,
					"bgcolour": ta.bg_color,
					"rotation": ta.rotation,
					"type": type,
					"inverted": ta.inverted,
					"transparent": ta.transparent
				}
				new_tl["text_areas"].append(new_ta)
			textlayer_output[pg.image_ref] = new_tl
	print(page_output)
	print(textlayer_output)
	print(fr_jm_output)
	with open("tests/results/body/test_body_pages.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(page_output, ensure_ascii=False))
	with open("tests/results/body/test_body_textlayers.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(textlayer_output, ensure_ascii=False))
	with open("tests/results/body/test_body_frames_jumps.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(fr_jm_output, ensure_ascii=False))

def test_body_images():
	op = {}
	for pg in list(iter(book_body)):
		img = pg.image
		op[pg.image_ref] = {
			"id": img.id,
			"type": img.type,
			"is_embedded": img.is_embedded,
			"filesize": img.filesize
		}
	print(op)
	with open("tests/results/body/test_body_images.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(op, ensure_ascii=False))
