from libacbf.Structs import Author
from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.ACBFBook import ACBFBook

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book: ACBFBook = ACBFBook(sample)
meta: ACBFMetadata = book.Metadata

print(meta.book_info.genres)
