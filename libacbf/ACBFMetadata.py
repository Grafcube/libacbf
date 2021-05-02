from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from libacbf.ACBFBook import ACBFBook

from libacbf.Constants import BookNamespace
from libacbf.MetadataInfo import BookInfo, PublishInfo, DocumentInfo

class ACBFMetadata:
	"""
	docstring
	"""
	def __init__(self, book: ACBFBook):
		ns: BookNamespace = book.namespace
		meta_root = book.root.find(f"{ns.ACBFns}meta-data")

		self.book_info: BookInfo = BookInfo(meta_root.find(f"{ns.ACBFns}book-info"), book)
		self.publisher_info: PublishInfo = PublishInfo(meta_root.find(f"{ns.ACBFns}publish-info"), book)
		self.document_info: DocumentInfo = DocumentInfo(meta_root.find(f"{ns.ACBFns}document-info"), book)
