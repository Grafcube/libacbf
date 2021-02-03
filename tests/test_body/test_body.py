import json
from libacbf.ACBFBook import ACBFBook

sample_path = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book = ACBFBook(sample_path)
book_body = book.Body
book_pages = book_body.pages

def test_body_info():
	print(book_body.bgcolor)
	print("Number of Pages: ", len(book_pages))
	with open("tests/results/body/test_body_info.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps({"bgcolour": book_body.bgcolor, "pages": len(book_pages)}, ensure_ascii=False))

def test_body_pages():
	output = []
	textlayer_output = {}
	for pg in book_pages:
		new_entry = {
			"bgcolour": pg.bg_color,
			"transition": str(pg.transition),
			"image": {
				"href": pg.image_ref
			},
			"title": {
				"titles": pg.title
			},
			"text_layer": {
				"text_layers": {}
			},
			"frame": {
				"frame": pg.frames
			},
			"jump": {
				"jumps": pg.jumps
			}
		}

		for tl in pg.text_layers.keys():
			new_tl = {
				"lang": pg.text_layers[tl].language,
				"bgcolour": pg.text_layers[tl].bg_color,
				"text_area": {
					"text_areas": []
				}
			}
			for ta in pg.text_layers[tl].text_areas:
				new_ta = {
					"points": ta.points,
					"p": {
						"paragraphs": ta.paragraph
					},
					"bgcolour": ta.bg_color,
					"rotation": ta.rotation,
					"type": str(ta.type),
					"inverted": ta.inverted,
					"transparent": ta.transparent
				}
				new_tl["text_area"]["text_areas"].append(new_ta)
			textlayer_output[new_entry["image"]["href"]] = new_tl
		output.append(new_entry)
	print(output)
	print(textlayer_output)
	with open("tests/results/body/test_body_pages.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(output, ensure_ascii=False))
	with open("tests/results/body/test_body_textlayers.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(textlayer_output, ensure_ascii=False))
