from libacbf.ACBFBook import ACBFBook
from libacbf.ACBFMetadata import ACBFMetadata

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book = ACBFBook(sample)
book_body = book.Body

page_stream = iter(book_body)

while True:
	try:
		print(next(page_stream).image_ref)
	except StopIteration:
		break
