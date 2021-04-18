from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.ACBFBook import ACBFBook
from libacbf.Editor import MetadataManager

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book: ACBFBook = ACBFBook(sample)
meta: ACBFMetadata = book.Metadata

mm = MetadataManager(book)

print(meta.book_info.book_title)
mm.edit_book_title("Another title")
mm.remove_book_title("en")
mm.remove_book_title()
mm.remove_book_title("sk")
print("after")
print(meta.book_info.book_title)
