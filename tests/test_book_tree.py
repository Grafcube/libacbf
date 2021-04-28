from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.ACBFBook import ACBFBook
from libacbf.Editor import MetadataManager

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book: ACBFBook = ACBFBook(sample)
meta: ACBFMetadata = book.Metadata
mm = MetadataManager(book)

print(meta.book_info.annotations)
print("\n")

mm.edit_annotation("This is an annotation.")

print("after")
print(meta.book_info.annotations)

mm.remove_annotation()

print("after")
print(meta.book_info.annotations)

mm.edit_annotation("ಇದು ಈ ಪುಸ್ತಕದ ವಿವರಣೆ", "kn")

print("after")
print(meta.book_info.annotations)
