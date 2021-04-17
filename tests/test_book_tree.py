from libacbf.Structs import Author
from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.ACBFBook import ACBFBook
from libacbf.Editor import MetadataManager

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book: ACBFBook = ACBFBook(sample)
meta: ACBFMetadata = book.Metadata

for i in meta.book_info.authors:
	print("fn:", i.first_name)
	print("mn:", i.middle_name)
	print("ln:", i.last_name)
	print("nn:", i.nickname)
	print("lang:", i.lang)
	print("act:", i.activity)
	print("hp:", i.home_page)
	print("em:", i.email)
	print('\n')

MetadataManager.add_book_author(meta, Author("AlsoHere"))
MetadataManager.remove_book_author(meta, 3)

print("after")
for i in meta.book_info.authors:
	print("fn:", i.first_name)
	print("mn:", i.middle_name)
	print("ln:", i.last_name)
	print("nn:", i.nickname)
	print("lang:", i.lang)
	print("act:", i.activity)
	print("hp:", i.home_page)
	print("em:", i.email)
	print('\n')
