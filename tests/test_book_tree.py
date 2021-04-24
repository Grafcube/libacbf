from libacbf.Structs import Genre
from libacbf.Constants import Genres
from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.ACBFBook import ACBFBook
from libacbf.Editor import MetadataManager

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book: ACBFBook = ACBFBook(sample)
meta: ACBFMetadata = book.Metadata
mm = MetadataManager(book)

for i in meta.book_info.genres.values():
	print("nm:", i.Genre)
	print("mt:", i.Match)

mm.add_genre(Genres.adventure)
mm.add_genre(Genre(Genres.fantasy, 42))

print("\nafter\n")
for i in meta.book_info.genres.values():
	print("nm:", i.Genre)
	print("mt:", i.Match)

mm.add_genre(Genre(Genres.fantasy, 78))
mm.add_genre(Genres.adventure)
mm.edit_genre_match(55, Genres.science_fiction)

print("\nafter\n")
for i in meta.book_info.genres.values():
	print("nm:", i.Genre)
	print("mt:", i.Match)

mm.remove_genre(Genres.fantasy)

print("\nafter\n")
for i in meta.book_info.genres.values():
	print("nm:", i.Genre)
	print("mt:", i.Match)

# Raises error as expected
# mm.edit_genre_match(100, Genres.fantasy)
