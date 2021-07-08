from zipfile import ZipFile
from libacbf import ACBFBook

def test_create_cbz(edit_dir):
	with ACBFBook(edit_dir/"test_create.cbz", 'w') as book:
		book.Metadata.book_info.edit_title("Test Create", "en")
		book.save(overwrite=True)
		book.Metadata.book_info.edit_annotation("This was created by a test.\nZip Archive.", "en")

def test_create_acbf(edit_dir):
	with ACBFBook(edit_dir/"test_create.acbf", 'w') as book:
		book.Metadata.book_info.edit_title("Test Create", "en")
		book.save(overwrite=True)
		book.Metadata.book_info.edit_annotation("This was created by a test.\nACBF XML File", "en")

def test_direct_cbz(edit_dir):
	zip = ZipFile(edit_dir/"test_direct.cbz", 'w')
	with ACBFBook(zip, 'w', direct=True)

def test_direct_cb7(edit_dir):
	pass

def test_direct_cbt(edit_dir):
	pass

def test_handle_bytes(edit_dir):
	pass
