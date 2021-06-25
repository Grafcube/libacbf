import os
import json
from pathlib import Path
from typing import Tuple
from libacbf import ACBFBook

# def make_editor_dir(path):
# 	os.makedirs(path/"editor", exist_ok=True)
# 	return path/"editor"

# def test_references(edit_books: Tuple[Path, ACBFBook]):
# 	path, book = edit_books

# 	op = {"original": book.References}

# 	book.edit_reference("test_ref", "This is a new test reference.")
# 	op["added"] = book.References

# 	book.edit_reference("electric_boogaloo", "This is another test reference.\nWith another line.")
# 	op["added"] = book.References

# 	book.edit_reference("tb_deleted", "This one will be deleted.")
# 	op["added"] = book.References

# 	book.edit_reference("test_ref", "This is an edited test reference.")
# 	op["edited"] = book.References

# 	book.remove_reference("tb_deleted")
# 	op["removed"] = book.References

# 	dir = make_editor_dir(path)
# 	with open(dir + "test_references.json", 'w', encoding="utf-8", newline='\n') as result:
# 		result.write(json.dumps(op, ensure_ascii=False))

# def test_data():
# 	pass

# def test_styles():
# 	pass
