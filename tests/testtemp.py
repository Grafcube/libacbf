import time
from libacbf import ACBFBook
from tests.testsettings import samples

with ACBFBook(samples[2]) as book:
	for i in book.Body.pages:
		print(i.image_ref, i.image.filesize)
	time.sleep(5)
