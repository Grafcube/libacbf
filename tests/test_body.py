import os
import json
import pytest
from pathlib import Path
from libacbf import ACBFBook
from tests.testres import samples


@pytest.mark.parametrize("dir", samples.values())
def test_body_info(dir, results):
    dir = Path(dir)
    op_path = results / "test_body" / dir.name
    os.makedirs(op_path, exist_ok=True)
    with ACBFBook(dir) as book:
        with open(op_path / "test_body_info.json", 'w', encoding="utf-8", newline='\n') as result:
            result.write(json.dumps({"bgcolour": book.body.bgcolor,
                                     "pages": len(book.body.pages)
                                     },
                                    ensure_ascii=False, indent='\t', separators=(', ', ': ')))


@pytest.mark.parametrize("dir", samples.values())
def test_body_pages(dir, results):
    dir = Path(dir)
    op_path = results / "test_body" / dir.name
    os.makedirs(op_path, exist_ok=True)

    page_output = {}
    textlayer_output = {}
    fr_jm_output = {"frames": {}, "jumps": {}}

    with ACBFBook(dir) as book:
        for pg in book.body.pages:
            new_pg = {
                "bgcolour": pg.bgcolor,
                "transition": pg.transition.name if pg.transition is not None else None,
                "ref_type": pg.ref_type.name,
                "titles": pg.title
                }
            page_output[pg.image_ref] = new_pg

            for fr in pg.frames:
                pts = [f"({x[0]},{x[1]})" for x in fr.points]
                fr_jm_output["frames"][pg.image_ref] = {"bgcolor": fr.bgcolor, "points": pts}

            for jm in pg.jumps:
                pts = [f"({x[0]},{x[1]})" for x in jm.points]
                fr_jm_output["jumps"][pg.image_ref] = {"page": jm.page, "points": pts}

            textlayer_output[pg.image_ref] = []
            for lang, tl in pg.text_layers.items():
                new_tl = {
                    "lang": lang,
                    "bgcolour": tl.bgcolor,
                    "text_areas": []
                    }

                for ta in tl.text_areas:
                    pts = [f"({x[0]},{x[1]})" for x in ta.points]

                    new_ta = {
                        "points": pts,
                        "p": ta.text,
                        "bgcolour": ta.bgcolor,
                        "rotation": ta.rotation,
                        "type": ta.type.name if ta.type is not None else None,
                        "inverted": ta.inverted,
                        "transparent": ta.transparent
                        }
                    new_tl["text_areas"].append(new_ta)
                textlayer_output[pg.image_ref].append(new_tl)

    with open(op_path / "test_body_pages.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(page_output, ensure_ascii=False, indent='\t', separators=(', ', ': ')))
    with open(op_path / "test_body_textlayers.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(textlayer_output, ensure_ascii=False, indent='\t', separators=(', ', ': ')))
    with open(op_path / "test_body_frames_jumps.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(fr_jm_output, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


@pytest.mark.parametrize("dir", samples.values())
def test_body_images(dir, results):
    dir = Path(dir)
    op_path = results / "test_body" / dir.name
    os.makedirs(op_path, exist_ok=True)

    op = {}
    with ACBFBook(dir) as book:
        for pg in book.body.pages:
            img = pg.image
            op[pg.image_ref] = {
                "id": img.id,
                "type": img.type,
                "is_embedded": img.is_embedded,
                "filesize": len(img.data)
                }

    with open(op_path / "test_body_images.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))
