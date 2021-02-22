from libacbf.ACBFBook import ACBFBook
from libacbf.ACBFMetadata import ACBFMetadata

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book = ACBFBook(sample)
book_metadata: ACBFMetadata = book.Metadata

print(book_metadata.book_info.cover_page.text_layers)
