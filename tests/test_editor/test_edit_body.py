import os
import json
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
        pg.text_layers["en"].insert_new_textarea(0, [(0, 0), (0, 1), (1, 1), (1, 0)],
                                                 "English Layer")

        pg.add_textlayer("kn")
        pg.text_layers["kn"].insert_new_textarea(0, [(0, 0), (0, 1), (1, 1), (1, 0)],
                                                 "ಕನ್ನಡದ ಲೆಯರ್")

        pg.add_textlayer("sk")
        pg.text_layers["sk"].insert_new_textarea(0, [(0, 0), (0, 1), (1, 1), (1, 0)], "தமிழ் லெயர்")

        pg.add_textlayer("jp")
        pg.text_layers["jp"].insert_new_textarea(0, [(0, 0), (0, 1), (1, 1), (1, 0)], "日本語のレイヤー")

        pg.remove_textlayer("jp")
        pg.change_textlayer_lang("sk", "ta")

def test_frames():
    with ACBFBook(edit_dir / "test_frames.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Frames")

        book.Body.pages[0].insert_new_frame()
        book.Body.pages[0].insert_new_frame()
        book.Body.pages[0].insert_new_frame()
        book.Body.pages[0].insert_new_frame()
        book.Body.pages[0].remove_frame()
        book.Body.pages[0].reorder_frame()

def test_jumps():
    with ACBFBook(edit_dir / "test_jumps.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Jumps")

        book.Body.pages[0].add_jump()
        book.Body.pages[0].add_jump()
        book.Body.pages[0].add_jump()
        book.Body.pages[0].add_jump()
        book.Body.pages[0].remove_jump()

def test_bgcolor():
    pass  # with ACBFBook(edit_dir / "test_bgcolor.acbf", 'w', archive_type=None) as book:  #  #
    #    book.Metadata.book_info.edit_title("Test Background Colours")  #  #         #  #  #  #
    #    Write cover, pages, Text layers, Text areas, Frames and Jumps here  #         #  #  #  #
    #    book.Body.set_bgcolor()  #
#         book.Body.pages[0].set_bgcolor()
#
#         book.Body.pages[0].set_bgcolor()
