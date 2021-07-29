import os
import json
from pathlib import Path
from typing import Tuple
from libacbf import ACBFBook


def make_body_dir(path):
    os.makedirs(path / "body", exist_ok=True)
    return path / "body"


def test_body_info(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_body_dir(path)
    with open(dir / "test_body_info.json", "w", encoding="utf-8", newline='\n') as result:
        result.write(json.dumps({"bgcolour": book.body.bgcolor, "pages": len(book.body.pages)},
                                ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_body_pages(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books

    page_output = {}
    textlayer_output = {}
    fr_jm_output = {"frames": {}, "jumps": {}}
    for pg in book.body.pages:
        transition = pg.transition.name if pg.transition is not None else None
        new_pg = {
            "bgcolour": pg.bgcolor,
            "transition": transition,
            "ref_type": pg.ref_type.name,
            "titles": pg.title
            }
        page_output[pg.image_ref] = new_pg

        for fr in pg.frames:
            pts = []
            for p in fr.points:
                pts.append(f"({p.x},{p.y})")

            new_fr = {"bgcolor": fr.bgcolor, "points": pts}
            fr_jm_output["frames"][pg.image_ref] = new_fr

        for jm in pg.jumps:
            pts = []
            for p in jm.points:
                pts.append(f"({p.x},{p.y})")

            new_jm = {"page": jm.page, "points": pts}
            fr_jm_output["jumps"][pg.image_ref] = new_jm

        textlayer_output[pg.image_ref] = []
        for tl in pg.text_layers.values():
            new_tl = {
                "lang": tl.language,
                "bgcolour": tl.bgcolor,
                "text_areas": []
                }
            for ta in tl.text_areas:
                pts = []
                for p in ta.points:
                    pts.append(f"({p.x},{p.y})")

                type = ta.type.name if ta.type is not None else None
                new_ta = {
                    "points": pts,
                    "p": ta.paragraph,
                    "bgcolour": ta.bgcolor,
                    "rotation": ta.rotation,
                    "type": type,
                    "inverted": ta.inverted,
                    "transparent": ta.transparent
                    }
                new_tl["text_areas"].append(new_ta)
            textlayer_output[pg.image_ref].append(new_tl)

    dir = make_body_dir(path)
    with open(dir / "test_body_pages.json", "w", encoding="utf-8", newline='\n') as result:
        result.write(
            json.dumps(page_output, ensure_ascii=False, indent='\t', separators=(', ', ': ')))
    with open(dir / "test_body_textlayers.json", "w", encoding="utf-8", newline='\n') as result:
        result.write(
            json.dumps(textlayer_output, ensure_ascii=False, indent='\t', separators=(', ', ': ')))
    with open(dir / "test_body_frames_jumps.json", "w", encoding="utf-8", newline='\n') as result:
        result.write(
            json.dumps(fr_jm_output, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_body_images(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books

    op = {}
    for pg in book.body.pages:
        img = pg.image
        op[pg.image_ref] = {
            "id": img.id,
            "type": img.type,
            "is_embedded": img.is_embedded,
            "filesize": len(img.data)
            }
    dir = make_body_dir(path)
    with open(dir / "test_body_images.json", "w", encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))
