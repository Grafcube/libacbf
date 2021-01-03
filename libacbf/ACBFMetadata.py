import pathlib
from datetime import date
import xmltodict
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

		if pathlib.Path(file_path).suffix != ".acbf":
			raise ValueError("File is not an ACBF Ebook")
		else:
			with open(file_path, encoding="utf-8") as book:
				try:
					xmltodict.parse(book.read(), item_depth=3, item_callback=get_metadata)
				except xmltodict.ParsingInterrupted:
					print("Finished parsing metadata")

		def get_metadata(path, item):
			if path[1][0] == "meta-data":
				self.book_info = BookInfoMetadata(item["book-info"])
				self.publisher_info = PublishInfoMetadata(item["publish-info"])
				self.document_info = DocumentInfoMetadata(item["document-info"])
				return False
			else:
				return True
