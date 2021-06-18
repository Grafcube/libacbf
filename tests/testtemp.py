from pprint import pprint
from libacbf import ACBFBook
from tests.testsettings import samples

with ACBFBook("temp/test.cbz", 'w') as book:
	pass
