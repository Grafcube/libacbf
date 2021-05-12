from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from libacbf.ACBFBook import ACBFBook

from libacbf.Constants import BookNamespace
from libacbf.MetadataInfo import BookInfo, PublishInfo, DocumentInfo

class ACBFMetadata:
	"""Class to read metadata from a book.

	See Also
	--------
	`Meta-data Section Definition <https://acbf.fandom.com/wiki/Meta-data_Section_Definition>`_.

	Attributes
	----------
	book : ACBFBook
		Book that this metadata belongs to.

	book_info : BookInfo
		See :class:`BookInfo <libacbf.MetadataInfo.BookInfo>`.

	publisher_info : BookInfo
		See :class:`PublishInfo <libacbf.MetadataInfo.PublishInfo>`.

	document_info : BookInfo
		See :class:`DocumentInfo <libacbf.MetadataInfo.DocumentInfo>`.
	"""
	def __init__(self, book: ACBFBook):
		self.book = book
		ns: BookNamespace = book.namespace
		meta_root = book._root.find(f"{ns.ACBFns}meta-data")

		self.book_info: BookInfo = BookInfo(meta_root.find(f"{ns.ACBFns}book-info"), book)
		self.publisher_info: PublishInfo = PublishInfo(meta_root.find(f"{ns.ACBFns}publish-info"), book)
		self.document_info: DocumentInfo = DocumentInfo(meta_root.find(f"{ns.ACBFns}document-info"), book)
