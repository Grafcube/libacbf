from libacbf.ACBFBook import ACBFBook
from libacbf.Editor import BookManager

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book: ACBFBook = ACBFBook(sample)

for i in book.Data.keys():
	print(i)
	print("id:", book.Data[i].id)
	print("ty:", book.Data[i].type)
	print("dt:", book.Data[i].data != "")
	print('\n')

BookManager.add_data(book, "tests/samples/cover.jpg")
BookManager.add_data(book, "tests/samples/JETBRAINSMONO-REGULAR.TTF")

for i in book.Data.keys():
	print(i)
	print("id:", book.Data[i].id)
	print("ty:", book.Data[i].type)
	print("dt:", book.Data[i].data != "")
	print('\n')

	with open(f"tests/results/editor/add_data_{book.Data[i].id}.txt", 'w', encoding="utf-8") as op:
		op.write(book.Data[i].data)
