import os
import json
import pytest
from pathlib import Path
from libacbf import ACBFBook
from tests.testres import samples


@pytest.mark.parametrize("dir", samples.values())
def test_styles(dir, results):
    dir = Path(dir)
    op_path = results / "test_styles" / dir.name
    os.makedirs(op_path / "stylesheets", exist_ok=True)
    with ACBFBook(dir) as book:
        with open(op_path / "list_styles.json", 'w', encoding="utf-8", newline='\n') as result:
            result.write(json.dumps(list(book.styles.list_styles()), ensure_ascii=False, indent='\t',
                                    separators=(', ', ': ')))

        for i in book.styles.list_styles():
            name = "embedded.css" if i == '_' else i
            with open(op_path / "stylesheets" / name, 'wb') as st_output:
                st_output.write(book.styles[i])
