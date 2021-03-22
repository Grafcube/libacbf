from libacbf.Structs import Author
from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.ACBFBook import ACBFBook

# sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book: ACBFBook = ACBFBook()
meta: ACBFMetadata = book.Metadata

meta.book_info.authors = [
	Author("Person", "A"),
	Author("Friend", "B"),
	Author(nickname="InsertBadJokeHere")
]

for i in meta.book_info.authors:
	print(i.__dict__)
