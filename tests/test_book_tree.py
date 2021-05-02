from libacbf.Structs import Author
from libacbf.Editor import MetadataManager
from libacbf.ACBFBook import ACBFBook

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book: ACBFBook = ACBFBook(sample)
mm = MetadataManager(book)

oa1 = book.Metadata.book_info.authors[4]
oa2 = 5

for i in book.Metadata.book_info.authors:
	print(i.first_name, i.last_name)
	print(i.nickname)
	print('')
print("after")

mm.edit_book_author(oa1, Author("a_firstname", "a_lastname", "a_nickname"))
mm.edit_book_author(oa2, Author("b_firstname", "b_lastname", "b_nickname"))

for i in book.Metadata.book_info.authors:
	print(i.first_name, i.last_name)
	print(i.nickname)
	print('')
