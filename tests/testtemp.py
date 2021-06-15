from pprint import pprint
from libacbf import ACBFBook
from tests.testsettings import samples

with ACBFBook(samples[1]) as book:
	for i in book.Body.pages:
		print(i.image_ref, len(i.image.data))
