from pprint import pprint
from libacbf import ACBFBook

with ACBFBook("temp/test_create.cbz", 'w') as book:
    book.Metadata.book_info.edit_title("Test Create", "en")
    book.save(overwrite=True)
    book.Metadata.book_info.edit_annotation("This was created by a test.\nZip Archive.", "en")
