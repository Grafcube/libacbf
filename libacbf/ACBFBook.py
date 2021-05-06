import os
from pathlib import Path
from typing import Dict, Optional, Union
from re import sub, findall, IGNORECASE
from lxml import etree
from zipfile import ZipFile
from py7zr import SevenZipFile
from rarfile import RarFile
from libacbf.Constants import BookNamespace
from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.ACBFBody import ACBFBody
from libacbf.ACBFData import ACBFData
from libacbf.Structs import Styles

class ACBFBook:
	"""
	docstring
	"""
	def __init__(self, file_path: str = "libacbf/templates/base_template_1.1.acbf"):
		self.is_open: bool = True

		self.book_path = os.path.abspath(file_path)

		self.archive: Optional[Union[ZipFile, SevenZipFile, RarFile]] = None

		self.file_path = Path(file_path)

		contents = None
		if self.file_path.suffix == ".acbf":
			with open(file_path, encoding="utf-8") as book:
				contents = book.read()

		elif self.file_path.suffix == ".cbz":
			self.archive = ZipFile(file_path, 'r')
			for i in self.archive.namelist():
				i = str(i)
				if "/" not in i and i.endswith(".acbf"):
					with self.archive.open(i, 'r') as book:
						contents = str(book.read(), "utf-8")
					break

		elif self.file_path.suffix == ".cb7":
			self.archive = SevenZipFile(self.book_path, 'r')
			for i in self.archive.getnames():
				if "/" not in i and i.endswith(".acbf"):
					contents = str(list(self.archive.read([i]).values())[0].read(), "utf-8")
					break

		elif self.file_path.suffix == ".cbr":
			pass

		else:
			raise ValueError("File is not an ACBF Ebook.")

		if contents is None:
			raise ValueError("File is not an ACBF Ebook.")

		self._root = etree.fromstring(bytes(contents, encoding="utf-8"))
		self._tree = self._root.getroottree()

		self._validate_acbf()

		self.namespace: BookNamespace = BookNamespace(f"{{{self._root.nsmap[None]}}}")

		self.Styles: Styles = Styles(self, findall(r'<\?xml-stylesheet type="text\/css" href="(.+)"\?>', contents, IGNORECASE))

		self.Metadata: ACBFMetadata = ACBFMetadata(self)

		self.Body: ACBFBody = ACBFBody(self)

		self.Data: ACBFData = ACBFData(self)

		self.Stylesheet: Optional[str] = None
		if self._root.find(f"{self.namespace.ACBFns}style") is not None:
			self.Stylesheet = self._root.find(f"{self.namespace.ACBFns}style").text.strip()

		self.References: Dict[str, Dict[str, str]] = self.sync_references()

	def sync_references(self) -> Dict[str, Dict[str, str]]:
		ns = self.namespace
		ref_root = self._root.find(f"{ns.ACBFns}references")
		references = {}
		if ref_root is None:
			return references
		reference_items = ref_root.findall(f"{ns.ACBFns}reference")
		for ref in reference_items:
			pa = []
			for p in ref.findall(f"{ns.ACBFns}p"):
				text = sub(r"<\/?p[^>]*>", "", str(etree.tostring(p, encoding="utf-8"), encoding="utf-8").strip())
				pa.append(text)
			references[ref.attrib["id"]] = {"paragraph": "\n".join(pa)}
		return references

	def save(self, path: str = "", overwrite: bool = True):
		if path == "":
			path = self.book_path

	def close(self):
		if self.archive is not None:
			self.archive.close()
			self.is_open = False

	def _validate_acbf(self):
		"""
		docstring
		"""
		version = self._tree.docinfo.xml_version
		xsd_path = f"libacbf/schema/acbf-{version}.xsd"

		with open(xsd_path, encoding="utf-8") as file:
			acbf_root = etree.fromstring(bytes(file.read(), encoding="utf-8"))
			acbf_tree = acbf_root.getroottree()
			acbf_schema = etree.XMLSchema(acbf_tree)

		# TODO fix schema error. When fixed, remove try/except
		try:
			acbf_schema.assertValid(self._tree)
		except etree.DocumentInvalid as err:
			print("Validation failed. File may be valid (bug)")
			print(err)

	def __enter__(self):
		return self

	def __exit__(self, exception_type, exception_value, traceback):
		self.close()
