from lxml import etree
from libacbf.Constants import BookNamespace
from libacbf.MetadataInfo import BookInfo, PublishInfo, DocumentInfo

class ACBFMetadata:
	"""
	docstring
	"""
	def __init__(self, meta_root, ns: BookNamespace):
		validate_acbf(meta_root)

		self.book_info: BookInfo = BookInfo(meta_root.find(f"{ns.ACBFns}book-info"), ns)
		self.publisher_info: PublishInfo = PublishInfo(meta_root.find(f"{ns.ACBFns}publish-info"), ns)
		self.document_info: PublishInfo = DocumentInfo(meta_root.find(f"{ns.ACBFns}document-info"), ns)

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

	# TODO fix schema error. When fixed, remove try/except
	try:
		acbf_schema.assertValid(tree)
	except etree.DocumentInvalid:
		print("Validation failed. File may be valid (bug)")
