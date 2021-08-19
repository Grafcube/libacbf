import os
import json
import pytest
from pathlib import Path
from libacbf import ACBFBook
from tests.testres import samples


@pytest.mark.parametrize("dir", samples.values())
def test_embedded(dir, results):
    dir = Path(dir)
    op_path = Path(results / "test_binary_data")
    os.makedirs(op_path, exist_ok=True)
    op = {}
    with ACBFBook(dir) as book:
        for i in book.data.list_files():
            op[i] = {
                "type": book.data[i].type,
                "is_embedded": book.data[i].is_embedded,
                "filesize": len(book.data[i].data)
                }
    with open(op_path / (dir.name + ".json"), 'w', encoding="utf-8", newline='\n') as result:
        result.write(json.dumps(op, ensure_ascii=False, indent='\t', separators=(', ', ': ')))
