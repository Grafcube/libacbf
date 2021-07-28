import os
import json
import pytest
from pathlib import Path
from libacbf import ACBFBook

edit_dir = Path("tests/results/edit_body/")
os.makedirs(edit_dir, exist_ok=True)


def test_images(abspath):
    with ACBFBook(edit_dir / "test_images.cbz", 'w') as book:
        book.Metadata.book_info.edit_title("Test Image Ref")

        book.Data.add_data("tests/samples/assets/cover.jpg")
        book.Data.add_data("tests/samples/assets/page1.jpg")
        book.Data.add_data("tests/samples/assets/page2.jpg", "img/page2.jpg")
        book.Data.add_data("tests/samples/assets/page3.jpg", embed=True)
        book.save()

        arcref = r"zip:tests/samples/Doctorow, Cory - Craphound - NoACBF.cbz!page4.jpg"
        url = r"https://upload.wikimedia.org/wikipedia/commons/c/cf/Afgretygh.png"

        book.Metadata.book_info.cover_page.set_image_ref("cover.jpg")
        book.Body.pages[0].set_image_ref("page1.jpg")
        book.Body.insert_new_page(1, "img/page2.jpg")
        book.Body.insert_new_page(2, "#page3.jpg")
        book.Body.insert_new_page(3, arcref)
        book.Body.insert_new_page(4, url)

        if abspath is not None:
            book.Body.insert_new_page(4, abspath)

        ops = {}
        cover = book.Metadata.book_info.cover_page.image
        ops[cover.id] = len(cover.data)
        for pg in book.Body.pages:
            ops[pg.image.id] = len(pg.image.data)

        with open(edit_dir / "test_images.json", 'w', encoding="utf-8") as op:
            op.write(json.dumps(ops, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_textlayers():
    with ACBFBook(edit_dir / "test_textlayers.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Text Layers")

        pg = book.Body.pages[0]

        pg.add_textlayer("en")
        pg.text_layers["en"].insert_new_textarea(0, [(0, 0), (0, 1), (1, 1), (1, 0)], "English Layer")

        pg.add_textlayer("kn")
        pg.text_layers["kn"].insert_new_textarea(0, [(0, 0), (0, 1), (1, 1), (1, 0)], "ಕನ್ನಡದ ಲೆಯರ್")

        pg.add_textlayer("sk")
        pg.text_layers["sk"].insert_new_textarea(0, [(0, 0), (0, 1), (1, 1), (1, 0)], "தமிழ் லெயர்")

        pg.add_textlayer("ja")
        pg.text_layers["ja"].insert_new_textarea(0, [(0, 0), (0, 1), (1, 1), (1, 0)], "日本語のレイヤー")

        pg.remove_textlayer("ja")
        pg.change_textlayer_lang("sk", "ta")


def test_textareas():
    with ACBFBook(edit_dir / "test_textareas.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Text Areas")

        book.Body.pages[0].add_textlayer("en")
        tl = book.Body.pages[0].text_layers["en"]

        tl.insert_new_textarea(0, [(0, 0), (0, 1), (1, 1), (1, 0)], "Area 1.")
        tl.insert_new_textarea(1, [(0, 0), (0, 1), (1, 1), (1, 0)], "SWAP 5.")
        tl.insert_new_textarea(2, [(0, 0), (0, 1), (1, 1), (1, 0)], "Area 3.")
        tl.insert_new_textarea(3, [(0, 0), (0, 1), (1, 1), (1, 0)], "Area 4.")
        tl.insert_new_textarea(4, [(0, 0), (0, 1), (1, 1), (1, 0)], "REMOVE ME.")
        tl.insert_new_textarea(5, [(0, 0), (0, 1), (1, 1), (1, 0)], "SWAP 2.")
        tl.insert_new_textarea(6, [(0, 0), (0, 1), (1, 1), (1, 0)], "Area 6.")

        tl.remove_textarea(4)
        tl.reorder_textarea(4, 1)
        tl.reorder_textarea(2, 4)


def test_textarea_props():
    with ACBFBook(edit_dir / "test_textarea_props.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Text Area Properties")

        book.Body.pages[0].add_textlayer("en")
        book.Body.pages[0].text_layers["en"].insert_new_textarea(0, [(0, 0), (0, 1), (1, 1), (1, 0)], "A new area.")
        ta = book.Body.pages[0].text_layers["en"].text_areas[0]

        ta.set_paragraph("An edited area.")
        ta.set_paragraph("An edited area\n...with a new line!!!")
        ta.set_paragraph("An edited area\n...with a new line!!!\nAnd fancy formatting: "
                         "<strong>strong</strong>, <emphasis>emphasis</emphasis>, "
                         "<strikethrough>strikethrough</strikethrough>, <sub>sub</sub>, "
                         '<sup>sup</sup>, <a href="a_reference_001" />')

        ta.append_point(2, 2)
        ta.insert_point(2, 3, 3)
        ta.set_point(1, 1, 0)
        ta.remove_point(4)

        ta.set_rotation(45)
        ta.set_rotation(None)
        ta.set_rotation(90)
        with pytest.raises(ValueError, match="Rotation must be an integer from 0 to 360."):
            ta.set_rotation(-1)
        with pytest.raises(ValueError, match="Rotation must be an integer from 0 to 360."):
            ta.set_rotation(361)

        ta.set_type("code")
        ta.set_type(None)
        ta.set_type("speech")

        ta.set_inverted(False)
        ta.set_inverted(None)
        ta.set_inverted(True)

        ta.set_transparent(False)
        ta.set_transparent(None)
        ta.set_transparent(True)


def test_frames():
    with ACBFBook(edit_dir / "test_frames.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Frames")

        book.Body.pages[0].insert_new_frame(0, [(0, 0), (0, 1), (1, 1), (1, 0)])  # Keep as is
        book.Body.pages[0].insert_new_frame(1, [(0, 0), (0, 1), (1, 1), (1, 0)])  # Edit to 2
        book.Body.pages[0].insert_new_frame(2, [(1, 1), (-1, 1), (-1, -1), (1, -1)])  # Reorder
        book.Body.pages[0].insert_new_frame(1, [(0, 0), (0, 1)])  # Insert
        book.Body.pages[0].insert_new_frame(-1, [(0, 0)])  # Remove me

        book.Body.pages[0].remove_frame(-2)

        book.Body.pages[0].reorder_frame(3, 1)

        book.Body.pages[0].frames[3].set_point(1, 0, 2)
        book.Body.pages[0].frames[3].set_point(2, 2, 2)
        book.Body.pages[0].frames[3].set_point(3, 2, 0)

        book.Body.pages[0].frames[3].insert_point(1, -2, -2)
        book.Body.pages[0].frames[3].insert_point(-1, 0, 0)

        book.Body.pages[0].frames[3].remove_point(-2)


def test_jumps():
    with ACBFBook(edit_dir / "test_jumps.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Jumps")

        book.Body.pages[0].add_jump(0, [(0, 0), (0, 1), (1, 1), (1, 0)])
        book.Body.pages[0].add_jump(1, [(0, 0), (0, 1), (1, 1), (1, 0)])
        book.Body.pages[0].add_jump(2, [(0, 0), (0, 1), (1, 1), (1, 0)])
        book.Body.pages[0].add_jump(1, [(0, 0)])

        book.Body.pages[0].remove_jump(-1)

        book.Body.pages[0].jumps[2].set_target_page(5)

        book.Body.pages[0].jumps[1].set_point(1, 0, 2)
        book.Body.pages[0].jumps[1].set_point(2, 2, 2)
        book.Body.pages[0].jumps[1].set_point(3, 2, 0)

        book.Body.pages[0].jumps[1].insert_point(-1, 3, 3)
        book.Body.pages[0].jumps[1].insert_point(-1, 0, 0)

        book.Body.pages[0].jumps[1].remove_point(-2)


def test_bgcolor():
    with ACBFBook(edit_dir / "test_bgcolor.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Background Colours")

        book.Body.set_bgcolor("#000000")
        book.Body.set_bgcolor(None)
        book.Body.set_bgcolor("#0000ff")

        book.Body.pages[0].set_bgcolor("#000000")
        book.Body.pages[0].set_bgcolor(None)
        book.Body.pages[0].set_bgcolor("#00ff00")

        book.Body.pages[0].add_textlayer("en")
        book.Body.pages[0].text_layers["en"].set_bgcolor("#000000")
        book.Body.pages[0].text_layers["en"].set_bgcolor(None)
        book.Body.pages[0].text_layers["en"].set_bgcolor("#00ffff")

        book.Body.pages[0].text_layers["en"].insert_new_textarea(0, [(0, 0)], "Testing background colour.")
        book.Body.pages[0].text_layers["en"].text_areas[0].set_bgcolor("#000000")
        book.Body.pages[0].text_layers["en"].text_areas[0].set_bgcolor(None)
        book.Body.pages[0].text_layers["en"].text_areas[0].set_bgcolor("#ff0000")

        book.Body.pages[0].insert_new_frame(0, [(0, 0)])
        book.Body.pages[0].frames[0].set_bgcolor("#000000")
        book.Body.pages[0].frames[0].set_bgcolor(None)
        book.Body.pages[0].frames[0].set_bgcolor("#ff00ff")
