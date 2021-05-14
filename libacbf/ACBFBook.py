import os
from pathlib import Path
from typing import Dict, Optional
from re import sub, findall, IGNORECASE
from lxml import etree

from libacbf.Constants import BookNamespace
from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.ACBFBody import ACBFBody
from libacbf.ACBFData import ACBFData
from libacbf.Structs import Styles
from libacbf.ArchiveReader import ArchiveReader

class ACBFBook:
	"""Base class for reading ACBF ebooks.

	Parameters
	----------
	file_path : str, default=Empty book template
		Path to ACBF book. May be absolute or relative.

	See Also
	--------
	`ACBF Specifications <https://acbf.fandom.com/wiki/Advanced_Comic_Book_Format_Wiki>`_.

	Examples
	--------
	A book object can be opened, read and then closed. It can read files with the extensions
	``.acbf``, ``.cbz``, ``.cb7``, ``.cbt``, ``.cbr``. ::

		from libacbf.ACBFBook import ACBFBook

		book = ACBFBook("path/to/file.cbz")
		# Read data from book
		book.close()

	``ACBFBook`` is also a context manager and can be used in with statements. ::

		from libacbf.ACBFBook import ACBFBook

		with ACBFBook("path/to/file.cbz") as book:
			# Read data from book

	Attributes
	----------
	Metadata : ACBFMetadata
		See :class:`ACBFMetadata<libacbf.ACBFMetadata.ACBFMetadata>` for more information.

	Body : ACBFBody
		See :class:`ACBFBody<libacbf.ACBFBody.ACBFBody>` for more information.

	Data : ACBFData
		See :class:`ACBFData<libacbf.ACBFData.ACBFData>` for more information.

	References : dict
		A dictionary that contains a list of particular references that occur inside the
		main document body. Keys are unique reference ids and values are dictionaries that contain
		a ``paragraph`` key with text. ::

			{
				"ref_id_001": {
					"paragraph": "This is a reference."
				}
				"ref_id_002": {
					"paragraph": "This is another reference."
				}
			}

		``paragraph`` can contain special tags for formatting. For more information and a full list,
		see :class:`TextArea<libacbf.BodyInfo.TextArea>`.

	Styles : dict-like object
		An object that behaves like a dictionary. Use ``Styles[file name]`` to get the contents of
		the stylesheet as a string. Use :meth:`list_styles() <libacbf.Structs.Styles.list_styles()>`
		to get list of all available styles. All paths are relative. ::

			style = book.Styles["style_name.css"]

	Stylesheet : str, optional
		Embedded stylesheet, if exists, as a string.

	archive : ArchiveReader, optional
		Can be used to read archive directly if file is not ``.acbf``.

		:attr:`ArchiveReader.archive <libacbf.ArchiveReader.ArchiveReader.archive>` may be
		``zipfile.ZipFile``, ``pathlib.Path``, ``tarfile.TarFile`` or ``rarfile.RarFile``.

	file_path : str
		Absolute path to source file.

	namespace : BookNamespace
		Namespace of ACBF XML file. Use :obj:`BookNamespace.ACBFns_raw <libacbf.Constants.BookNamespace.ACBFns_raw>`
		to get namespace as string.
	"""
	def __init__(self, file_path: str = "libacbf/templates/base_template_1.1.acbf"):
		self.is_open: bool = True

		self.book_path = Path(file_path)

		self.file_path = os.path.abspath(file_path)

		self.archive: Optional[ArchiveReader] = None

		contents = None
		if self.book_path.suffix == ".acbf":
			with open(file_path, encoding="utf-8") as book:
				contents = book.read()

		elif self.book_path.suffix in [".cbz", ".cb7", ".cbt", ".cbr"]:
			self.archive = ArchiveReader(file_path)
			contents = self.archive._get_acbf_contents()
			if contents is None:
				raise ValueError("File is not an ACBF Ebook.")

		else:
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

	def close(self):
		"""Closes open archives if file is ``.cbz``, ``.cbt`` or ``.cbr``. Removes temporary
		directory for ``.cb7`` files.
		"""
		if self.archive is not None:
			self.archive.close()
			self.is_open = False

	def save(self, path: str = "", overwrite: bool = False):
		# To be called by Editor class
		if path == "":
			path = self.file_path
		raise NotImplementedError

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

	def _validate_acbf(self):
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
