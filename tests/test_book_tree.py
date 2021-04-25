from libacbf.ACBFBook import ACBFBook
from libacbf.Editor import BookManager

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book: ACBFBook = ACBFBook(sample)
bm = BookManager(book)

for i in book.Data.keys():
	print(i)
	print("id:", book.Data[i].id)
	print("ty:", book.Data[i].type)
	print('\n')

bm.add_data("tests/samples/JETBRAINSMONO-REGULAR.TTF")
dt = None

for i in book.Data.keys():
	print(i)
	print("id:", book.Data[i].id)
	print("ty:", book.Data[i].type)
	dt = book.Data[i].data
	print('\n')

with open("tests/results/op.ttf", 'wb') as img:
	img.write(dt.getvalue())
