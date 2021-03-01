import json
from libacbf.ACBFBook import ACBFBook

sample_path = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book = ACBFBook(sample_path)
book_body = book.Body
book_pages = book_body.pages

def test_body_info():
	print(book_body.bgcolor)
	print("Number of Pages: ", book_body.total_pages)
	with open("tests/results/body/test_body_info.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps({"bgcolour": book_body.bgcolor, "pages": book_body.total_pages}, ensure_ascii=False))

def test_body_pages():
	output = []
	textlayer_output = {}
	print(len(list(book_body)))
	for pg in book_pages.values():
		new_entry = {
			"bgcolour": pg.bg_color,
			"transition": str(pg.transition),
			"image": pg.image_ref,
			"titles": pg.title,
			"text_layers": {},
			"frames": [],
			"jumps": []
		}

		for fr in pg.frames:
			new_fr = {
				"bgcolor": fr.bgcolor,
				"points": fr.points
			}
			new_entry["frames"].append(new_fr)

		for jm in pg.jumps:
			new_jm = {
				"page": jm.page,
				"points": jm.points
			}
			new_entry["jumps"].append(new_jm)

		for tl in pg.text_layers.keys():
			new_tl = {
				"lang": pg.text_layers[tl].language,
				"bgcolour": pg.text_layers[tl].bg_color,
				"text_areas": []
			}
			for ta in pg.text_layers[tl].text_areas:
				new_ta = {
					"points": ta.points,
					"p": ta.paragraph,
					"bgcolour": ta.bg_color,
					"rotation": ta.rotation,
					"type": str(ta.type),
					"inverted": ta.inverted,
					"transparent": ta.transparent
				}
				new_tl["text_areas"].append(new_ta)
			textlayer_output[new_entry["image"]] = new_tl
		output.append(new_entry)
	print(output)
	print(textlayer_output)
	with open("tests/results/body/test_body_pages.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(output, ensure_ascii=False))
	with open("tests/results/body/test_body_textlayers.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(textlayer_output, ensure_ascii=False))
