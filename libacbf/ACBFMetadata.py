import pathlib
from lxml import etree
from libacbf.MetadataInfo import BookInfo, PublishInfo, DocumentInfo

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
			with open(file_path, encoding="utf-8") as book:
				root = etree.fromstring(bytes(book.read(), encoding="utf-8"))
				validate_acbf(root)

				ACBFns = r"{" + root.nsmap[None] + r"}"

				self.book_info = BookInfo(root.find(f"{ACBFns}meta-data/{ACBFns}book-info"), ACBFns)
				self.publisher_info = PublishInfo(root.find(f"{ACBFns}meta-data/{ACBFns}publish-info"), ACBFns)
				self.document_info = DocumentInfo(root.find(f"{ACBFns}meta-data/{ACBFns}document-info"), ACBFns)

def validate_acbf(root):
		"""
		docstring
		"""
		tree = root.getroottree()
		version = tree.docinfo.xml_version
		xsd_path = f"libacbf/schema/acbf-{version}.xsd"

		with open(xsd_path, encoding="utf-8") as file:
			acbf_root = etree.XML(bytes(file.read(), encoding="utf-8"))
			acbf_tree = acbf_root.getroottree()
			acbf_schema = etree.XMLSchema(acbf_tree)

		try:
			acbf_schema.assertValid(tree)
		except etree.DocumentInvalid:
			print("Validation failed. File may be valid (bug)") # TODO fix whatever
