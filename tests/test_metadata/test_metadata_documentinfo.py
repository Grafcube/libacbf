import json
from tests.conftest import get_au_op
from libacbf import ACBFBook
from tests.testres import samples


def test_authors(results_documentinfo):
    with ACBFBook(samples["cbz"]) as book:
        op = [get_au_op(x) for x in book.document_info.authors]
        with open(results_documentinfo / "test_authors.json", 'w', encoding="utf-8", newline='\n') as result:
            result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_creation_date_string(results_documentinfo):
    with ACBFBook(samples["cbz"]) as book:
        with open(results_documentinfo / "test_creation_date_string.txt", 'w', encoding="utf-8",
                  newline='\n') as result:
            result.write(book.document_info.creation_date)


def test_creation_date(results_documentinfo):
    with ACBFBook(samples["cbz"]) as book:
        with open(results_documentinfo / "test_creation_date.txt", 'w', encoding="utf-8", newline='\n') as result:
            result.write(str(book.document_info.creation_date_value))


def test_source(results_documentinfo):
    with ACBFBook(samples["cbz"]) as book:
        with open(results_documentinfo / "test_source.txt", 'w', encoding="utf-8", newline='\n') as result:
            result.write(book.document_info.source)


def test_id(results_documentinfo):
    with ACBFBook(samples["cbz"]) as book:
        with open(results_documentinfo / "test_id.txt", 'w', encoding="utf-8", newline='\n') as result:
            result.write(book.document_info.document_id)


def test_version(results_documentinfo):
    with ACBFBook(samples["cbz"]) as book:
        with open(results_documentinfo / "test_version.txt", 'w', encoding="utf-8", newline='\n') as result:
            result.write(book.document_info.document_version)


def test_history(results_documentinfo):
    with ACBFBook(samples["cbz"]) as book:
        with open(results_documentinfo / "test_history.json", 'w', encoding="utf-8", newline='\n') as result:
            result.write(json.dumps(book.document_info.document_history, ensure_ascii=False, indent='\t',
                                    separators=(', ', ': ')))
