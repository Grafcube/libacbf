import json
from tests.conftest import get_au_op
from libacbf import ACBFBook
from tests.testres import samples


def test_authors(results_bookinfo):
    with ACBFBook(samples["cbz"]) as book:
        op = [get_au_op(x) for x in book.book_info.authors]
        with open(results_bookinfo / "test_authors.json", 'w', encoding="utf-8", newline='\n') as result:
            result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_titles(results_bookinfo):
    with ACBFBook(samples["cbz"]) as book:
        with open(results_bookinfo / "test_titles.json", 'w', encoding="utf-8", newline='\n') as result:
            result.write(json.dumps(book.book_info.book_title, ensure_ascii=False, indent='\t',
                                    separators=(', ', ': ')))


def test_genres(results_bookinfo):
    with ACBFBook(samples["cbz"]) as book:
        op = {k.name: v for k, v in book.book_info.genres.items()}
        with open(results_bookinfo / "test_genres.json", 'w', encoding="utf-8", newline='\n') as result:
            result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_annotations(results_bookinfo):
    with ACBFBook(samples["cbz"]) as book:
        with open(results_bookinfo / "test_annotations.json", 'w', encoding="utf-8", newline='\n') as result:
            result.write(json.dumps(book.book_info.annotations, ensure_ascii=False, indent='\t',
                                    separators=(', ', ': ')))


def test_languages(results_bookinfo):
    with ACBFBook(samples["cbz"]) as book:
        op = [{x.lang: x.show} for x in book.book_info.languages]
        with open(results_bookinfo / "test_languages.json", 'w', encoding="utf-8", newline='\n') as result:
            result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_characters(results_bookinfo):
    with ACBFBook(samples["cbz"]) as book:
        with open(results_bookinfo / "test_characters.json", 'w', encoding="utf-8", newline='\n') as result:
            result.write(json.dumps(book.book_info.characters, ensure_ascii=False, indent='\t',
                                    separators=(', ', ': ')))


def test_keywords(results_bookinfo):
    with ACBFBook(samples["cbz"]) as book:
        with open(results_bookinfo / "test_keywords.json", 'w', encoding="utf-8", newline='\n') as result:
            result.write(json.dumps(book.book_info.keywords, default=list, ensure_ascii=False, indent='\t',
                                    separators=(', ', ': ')))


def test_series(results_bookinfo):
    with ACBFBook(samples["cbz"]) as book:
        op = {k: {"sequence": v.sequence, "volume": v.volume} for k, v in book.book_info.series.items()}
        with open(results_bookinfo / "test_series.json", 'w', encoding="utf-8", newline='\n') as result:
            result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_content_rating(results_bookinfo):
    with ACBFBook(samples["cbz"]) as book:
        with open(results_bookinfo / "test_content_rating.json", 'w', encoding="utf-8", newline='\n') as result:
            result.write(json.dumps(book.book_info.content_rating, ensure_ascii=False, indent='\t',
                                    separators=(', ', ': ')))


def test_database_ref(results_bookinfo):
    with ACBFBook(samples["cbz"]) as book:
        op = [{"dbname": x.dbname, "ref": x.reference, "type": x.type} for x in book.book_info.database_ref]
        with open(results_bookinfo / "test_database_ref.json", 'w', encoding="utf-8", newline='\n') as result:
            result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_coverpage(results_bookinfo):
    page_output = {}
    textlayer_output = {}
    fr_jm_output = {"frames": {}, "jumps": {}}

    with ACBFBook(samples["cbz"]) as book:
        pg = book.book_info.coverpage

        page_output["image_ref"] = pg.image_ref
        page_output["ref_type"] = pg.ref_type.name
        page_output["image"] = len(pg.image.data)

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

    with open(results_bookinfo / "test_cover_pages.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(page_output, ensure_ascii=False, indent='\t', separators=(', ', ': ')))
    with open(results_bookinfo / "test_cover_textlayers.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(textlayer_output, ensure_ascii=False, indent='\t', separators=(', ', ': ')))
    with open(results_bookinfo / "test_cover_frames_jumps.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(fr_jm_output, ensure_ascii=False, indent='\t', separators=(', ', ': ')))
