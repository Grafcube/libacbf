from libacbf.ACBFBook import ACBFBook
from libacbf.Editor import BookManager

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book: ACBFBook = ACBFBook(sample)
data = book.Data
bm = BookManager(book)

bm.add_data(r"tests/samples/JetBrainsMono[wght].ttf")
print(len(data))
print(data.list_files())
print(data["JetBrainsMono[wght].ttf"].type)
