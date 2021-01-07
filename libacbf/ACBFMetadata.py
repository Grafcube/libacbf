import pathlib
from datetime import date
from lxml import etree
from libacbf import BookInfoMetadata, PublishInfoMetadata, DocumentInfoMetadata

class ACBFMetadata:
	"""
	docstring
	"""
	def __init__(self, file_path: str):
		"""
		docstring
		"""
		self.book_path = file_path

		self.book_info = None
		self.publisher_info = None
		self.document_info = None

		if pathlib.Path(file_path).suffix != ".acbf": # TODO cbz handling
			raise ValueError("File is not an ACBF Ebook")
		else:
			ACBFns = r"{http://www.fictionbook-lib.org/xml/acbf/1.0}"
			with open(file_path, encoding="utf-8") as book:
				root = etree.fromstring(bytes(book.read(), encoding="utf-8"))
				self.book_info = BookInfoMetadata(root.find(f"{ACBFns}meta-data/book-info"))
				self.publisher_info = PublishInfoMetadata(root.find(f"{ACBFns}meta-data/publish-info"))
				self.document_info = DocumentInfoMetadata(root.find(f"{ACBFns}meta-data/document-info"))
