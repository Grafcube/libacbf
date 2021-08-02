import os
import json
from pathlib import Path
from typing import Tuple
from tests.conftest import get_au_op
from libacbf import ACBFBook


def make_bookinfo_dir(path):
    os.makedirs(path / "metadata/book_info/", exist_ok=True)
    return path / "metadata/book_info/"


def test_authors(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    op = [get_au_op(x) for x in book.book_info.authors]
    dir = make_bookinfo_dir(path)
    with open(dir / "test_bookinfo_authors.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_titles(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_bookinfo_dir(path)
    with open(dir / "test_bookinfo_titles.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(book.book_info.book_title, ensure_ascii=False, indent='\t',
                                separators=(', ', ': ')))


def test_genres(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    genres = book.book_info.genres.values()
    op = {x.genre.name: x.match for x in genres}

    dir = make_bookinfo_dir(path)
    with open(dir / "test_bookinfo_genres.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_annotations(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_bookinfo_dir(path)
    with open(dir / "test_bookinfo_annotations.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(book.book_info.annotations, ensure_ascii=False, indent='\t',
                                separators=(', ', ': ')))


def test_languages(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    op = [{x.lang: x.show} for x in book.book_info.languages]
    dir = make_bookinfo_dir(path)
    with open(dir / "test_bookinfo_languages.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_characters(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_bookinfo_dir(path)
    with open(dir / "test_bookinfo_characters.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(book.book_info.characters, ensure_ascii=False, indent='\t',
                                separators=(', ', ': ')))


def test_keywords(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    op = book.book_info.keywords
    dir = make_bookinfo_dir(path)
    with open(dir / "test_bookinfo_keywords.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(op, default=list, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_series(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    series = book.book_info.series.values()
    op = {x.title: {"sequence": x.sequence, "volume": x.volume} for x in series}
    dir = make_bookinfo_dir(path)
    with open(dir / "test_bookinfo_series.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_content_rating(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    dir = make_bookinfo_dir(path)
    with open(dir / "test_bookinfo_content_rating.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(book.book_info.content_rating, ensure_ascii=False, indent='\t',
                                separators=(', ', ': ')))


def test_database_ref(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    op = []
    for i in book.book_info.database_ref:
        new_op = {"dbname": i.dbname, "text": i.reference, "type": i.type}
        op.append(new_op)

    dir = make_bookinfo_dir(path)
    with open(dir / "test_bookinfo_database_ref.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_coverpage(read_books: Tuple[Path, ACBFBook]):
    path, book = read_books
    page_output = {}
    textlayer_output = {}
    fr_jm_output = {"frames": {}, "jumps": {}}

    pg = book.book_info.cover_page

    page_output["image_ref"] = pg.image_ref
    page_output["ref_type"] = pg.ref_type.name

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

    for tl in pg.text_layers.keys():
        new_tl = {
            "lang": pg.text_layers[tl].lang,
            "bgcolour": pg.text_layers[tl].bgcolor,
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
                "bgcolour": ta.bgcolor,
                "rotation": ta.rotation,
                "type": type,
                "inverted": ta.inverted,
                "transparent": ta.transparent
                }
            new_tl["text_areas"].append(new_ta)
        textlayer_output[pg.image_ref] = new_tl

    dir = make_bookinfo_dir(path)
    with open(dir / "test_cover_page.json", "w", encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(page_output, ensure_ascii=False, indent='\t', separators=(', ', ': ')))
    with open(dir / "test_cover_textlayers.json", "w", encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(textlayer_output, ensure_ascii=False, indent='\t', separators=(', ', ': ')))
    with open(dir / "test_cover_frames_jumps.json", "w", encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(fr_jm_output, ensure_ascii=False, indent='\t', separators=(', ', ': ')))
