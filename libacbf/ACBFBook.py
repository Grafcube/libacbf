import pathlib
from lxml import etree
from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.ACBFBody import ACBFBody

class ACBFBook:
	"""
	docstring
	"""
	def __init__(self, file_path):
		self.book_path = file_path

		self.tree = None
		self.root = None
		self.namespace = None

		if pathlib.Path(file_path).suffix != ".acbf": # TODO cbz handling
			raise ValueError("File is not an ACBF Ebook")
		else:
			with open(file_path, encoding="utf-8") as book:
				self.root = etree.fromstring(bytes(book.read(), encoding="utf-8"))
				self.tree = self.root.getroottree()
				self.namespace = r"{" + self.root.nsmap[None] + r"}"

		self.Metadata: ACBFMetadata = ACBFMetadata(self.root.find(f"{self.namespace}meta-data"), self.namespace)

		self.Body: ACBFBody = None # TBD
