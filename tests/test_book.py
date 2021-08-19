import os
import pytest
import json
from pathlib import Path
from libacbf import ACBFBook
from libacbf.exceptions import InvalidBook
from tests.testres import samples, fail


@pytest.mark.parametrize("dir", samples.values())
def test_book_props(dir):
    with ACBFBook(dir) as book:
        dir = Path("tests/results") / Path(dir).name
        os.makedirs(dir, exist_ok=True)
        op = {
            "book_path": str(book.book_path),
            "archive_name": book.archive.filename if book.archive is not None else None,
            "archive_type": book.archive.type.name if book.archive is not None else None
            }
    with open(dir / "test_book_props.json", 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_no_acbf():
    with pytest.raises(InvalidBook):
        with ACBFBook(fail) as _:
            pass
