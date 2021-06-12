from pprint import pprint
from libacbf import ACBFBook
from tests.testsettings import samples

# with ACBFBook(samples[1]) as book:
# 	pprint(book.Metadata.book_info.authors[0].__dict__)

a = ["thing", "Thing", "ThinG", "Another", "one-more", "another thing"]

a = {x.lower() for x in a}

print(a, type(a))
