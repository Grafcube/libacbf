import json
from libacbf import ACBFBook
from tests.testres import samples


def test_references(results):
    with ACBFBook(samples["cbz"]) as book:
        with open(results / "test_references.json", 'w', encoding="utf-8", newline='\n') as result:
            result.write(json.dumps(book.references, ensure_ascii=False, indent='\t', separators=(', ', ': ')))
