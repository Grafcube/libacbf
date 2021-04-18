from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.Structs import Author
from libacbf.ACBFBook import ACBFBook
from libacbf.Editor import BookManager, MetadataManager

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book: ACBFBook = ACBFBook(sample)
meta: ACBFMetadata = book.Metadata

bm = BookManager(book)
# print(book.References.keys())
# bm.add_reference("test_id", "This is a reference for testing.")
# bm.remove_reference("ref_001")
# print(book.References.keys())

bm.add_data()
bm.remove_data()

# mm = MetadataManager(book)
# for i in meta.book_info.authors:
# 	print("fn", i.first_name)
# 	print("ln", i.last_name)
# 	print("nn", i.nickname)
# 	print("\n")
# mm.add_book_author(Author("AlsoHere"))
# mm.remove_book_author(3)
# print("after")
# for i in meta.book_info.authors:
# 	print("fn", i.first_name)
# 	print("ln", i.last_name)
# 	print("nn", i.nickname)
# 	print("\n")
