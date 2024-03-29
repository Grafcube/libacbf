import json
from pathlib import Path
from libacbf import ACBFBook


def test_pages(results_body):
    with ACBFBook(results_body / "test_pages.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Pages"

        book.body.append_page("page1")
        book.body.append_page("page2")
        book.body.append_page("page4")
        book.body.append_page("REMOVE_ME")
        book.body.append_page("page5")
        book.body.insert_page(2, "page3")

        book.body.pages.pop(4)

        book.body.pages[0].set_transition("scroll_right")

        book.body.pages[0].title['_'] = "Test Page"
        book.body.pages[0].title["en"] = "First Page"


def test_images(results_body, results, samples):
    with ACBFBook(results_body / "test_images.cbz", 'w') as book:
        book.book_info.book_title['_'] = "Test Image Ref"

        book.data.add_data(samples / "cover.jpg")
        book.data.add_data(samples / "page1.jpg")
        book.data.add_data(samples / "page2.jpg", "img/page2.jpg")
        book.data.add_data(samples / "page3.jpg", embed=True)

        arcref = f"zip:{results}/fail.cbz!page4.jpg"
        url = r"https://upload.wikimedia.org/wikipedia/commons/8/84/Example.svg"
        abspath = str(Path(samples / "page5.jpg").resolve(True))

        book.book_info.coverpage.image_ref = "cover.jpg"
        book.body.append_page("page1.jpg")
        book.body.append_page("img/page2.jpg")
        book.body.append_page("#page3.jpg")
        book.body.append_page(arcref)
        book.body.append_page(url)
        book.body.append_page(abspath)

        assert all([x.ref_type.name == "SelfArchived" for x in [book.book_info.coverpage] + book.body.pages[:1]])
        assert book.body.pages[2].ref_type.name == "Embedded"
        assert book.body.pages[3].ref_type.name == "Archived"
        assert book.body.pages[4].ref_type.name == "URL"
        assert book.body.pages[5].ref_type.name == "Local"

        ops = {}
        cover = book.book_info.coverpage
        ops[cover.image_ref] = len(cover.image.data)
        for pg in book.body.pages:
            ops[pg.image_ref] = len(pg.image.data)

        with open(results_body / "test_images.json", 'w', encoding="utf-8") as op:
            op.write(json.dumps(ops, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_textlayers(results_body):
    with ACBFBook(results_body / "test_textlayers.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Text Layers"

        book.body.append_page('')
        pg = book.body.pages[-1]

        pg.add_textlayer("en")
        pg.text_layers["en"].append_textarea("English Layer", [(0, 0), (0, 1), (1, 1), (1, 0)])

        pg.add_textlayer("kn")
        pg.text_layers["kn"].append_textarea("ಕನ್ನಡದ ಲೆಯರ್", [(0, 0), (0, 1), (1, 1), (1, 0)])

        pg.add_textlayer("ta")
        pg.text_layers["ta"].append_textarea("தமிழ் லெயர்", [(0, 0), (0, 1), (1, 1), (1, 0)])

        pg.add_textlayer("ja")
        pg.text_layers["ja"].append_textarea("日本語のレイヤー", [(0, 0), (0, 1), (1, 1), (1, 0)])

        pg.text_layers.pop("ja")


def test_textareas(results_body):
    with ACBFBook(results_body / "test_textareas.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Text Areas"

        book.body.append_page('')
        pg = book.body.pages[-1]

        pg.add_textlayer("en")
        tl = pg.text_layers["en"]

        tl.append_textarea("Area 1.", [(0, 0), (0, 1), (1, 1), (1, 0)])
        tl.append_textarea("Area 3.", [(0, 0), (0, 1), (1, 1), (1, 0)])
        tl.append_textarea("REMOVE ME.", [(0, 0), (0, 1), (1, 1), (1, 0)])
        tl.append_textarea("Area 4.", [(0, 0), (0, 1), (1, 1), (1, 0)])
        tl.insert_textarea(1, "Area 2.", [(0, 0), (0, 1), (1, 1), (1, 0)])

        tl.text_areas.pop(3)


def test_textarea_props(results_body):
    with ACBFBook(results_body / "test_textarea_props.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Text Area Properties"

        book.body.append_page('')
        pg = book.body.pages[-1]

        pg.add_textlayer("en")
        pg.text_layers["en"].append_textarea("A new area.", [(0, 0), (0, 1), (1, 1), (1, 0)])
        ta = pg.text_layers["en"].text_areas[0]

        ta.text = "An area\n...with a new line!!!\nAnd fancy formatting: " \
                  "<strong>strong</strong>, <emphasis>emphasis</emphasis>, " \
                  "<strikethrough>strikethrough</strikethrough>, <sub>sub</sub>, " \
                  '<sup>sup</sup>, <a href="a_reference_001" />'

        ta.points.append((5, 5))
        ta.rotation = 45
        ta.set_type("speech")
        ta.inverted = True
        ta.transparent = True


def test_frames(results_body):
    with ACBFBook(results_body / "test_frames.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Frames"

        book.body.append_page('')
        pg = book.body.pages[-1]

        pg.append_frame([(0, 0), (0, 1), (1, 1), (1, 0)])
        pg.append_frame([(1, 1), (-1, 1), (-1, -1), (1, -1)])
        pg.insert_frame(1, [(0, 0), (0, 1)])
        pg.append_frame([(0, 0)])

        pg.frames.pop(-1)


def test_jumps(results_body):
    with ACBFBook(results_body / "test_jumps.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Jumps"

        book.body.append_page('')
        pg = book.body.pages[-1]

        pg.add_jump(0, [(0, 0), (0, 1), (1, 1), (1, 0)])
        pg.add_jump(1, [(0, 0), (0, 1), (1, 1), (1, 0)])
        pg.add_jump(2, [(0, 0), (0, 1), (1, 1), (1, 0)])
        pg.add_jump(1, [(0, 0)])

        pg.jumps.pop(-1)

        pg.jumps[2].target = 5


def test_bgcolor(results_body):
    with ACBFBook(results_body / "test_bgcolor.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Background Colours"

        book.body.bgcolor = "#000000"

        book.body.append_page('')
        pg = book.body.pages[-1]
        pg.bgcolor = "#0000ff"

        pg.add_textlayer("en")
        tl = pg.text_layers["en"]
        tl.bgcolor = "#00ff00"

        tl.append_textarea("Testing background colour.", [(0, 0)])
        ta = tl.text_areas[-1]
        ta.bgcolor = "#00ffff"

        pg.append_frame([(0, 0)])
        pg.frames[0].bgcolor = "#ff0000"
