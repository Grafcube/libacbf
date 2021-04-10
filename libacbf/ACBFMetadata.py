from lxml import etree
from libacbf.Constants import BookNamespace
from libacbf.MetadataInfo import BookInfo, PublishInfo, DocumentInfo

class ACBFMetadata:
	"""
	docstring
	"""
	def __init__(self, meta_root, ns: BookNamespace):
		self._ns = ns

		self.book_info: BookInfo = BookInfo(meta_root.find(f"{ns.ACBFns}book-info"), ns)
		self.publisher_info: PublishInfo = PublishInfo(meta_root.find(f"{ns.ACBFns}publish-info"), ns)
		self.document_info: DocumentInfo = DocumentInfo(meta_root.find(f"{ns.ACBFns}document-info"), ns)
