import os
import pytest
import json
from pathlib import Path
from libacbf import ACBFBook
from tests.testres import samples, fail
from libacbf.exceptions import InvalidBook


@pytest.mark.parametrize("dir", samples.values())
def test_read_books(dir, results):
    dir = Path(dir)
    op_path = results / "test_read_books"
    os.makedirs(op_path, exist_ok=True)
    with ACBFBook(dir) as book:
        op = {
            "book_path": str(book.book_path),
            "archive_name": book.archive.filename if book.archive is not None else None,
            "archive_type": book.archive.type.name if book.archive is not None else None
            }
        with open(op_path / (dir.name + ".json"), 'w', encoding="utf-8", newline='\n') as result:
            result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))


def test_no_acbf():
    with pytest.raises(InvalidBook):
        with ACBFBook(fail) as _:
            pass
