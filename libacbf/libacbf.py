import os
import re
import warnings
import magic
from io import TextIOBase
from pathlib import PurePath
from typing import List, Dict, Optional, Union, IO
from lxml import etree

from libacbf.structs import Styles
from libacbf.metadata import BookInfo, PublishInfo, DocumentInfo
from libacbf.body import Page
from libacbf.bookdata import BookData
from libacbf.archivereader import ArchiveReader

def is_book_text(file: Union[str, PurePath, IO]) -> Optional[bool]:
	"""Check if file is a valid ACBF Ebook and if it is a text file or archive.

	Parameters
	----------
	file : Union[str, PurePath]
		Path to file.

	Returns
	-------
	bool | None
		Returns ``None`` if file is not a valid ACBF book. Returns ``True`` if book is an archive.
		Returns ``False`` if file is a text file.
	"""
	if isinstance(file, TextIOBase):
		return True

	if not isinstance(file, (str, PurePath)):
		file.seek(0)
		mime_type = magic.from_buffer(file.read(2048), True)
		file.seek(0)
	else:
		mime_type = magic.from_file(str(file), True)

	return mime_type.startswith("text/")

def _validate_acbf(root, ns: str):
	tree = root.getroottree()
	version = re.split(r'/', re.sub(r'\{|\}', "", ns))[-1]
	xsd_path = f"libacbf/schema/acbf-{version}.xsd"

	with open(xsd_path, encoding="utf-8") as file:
		acbf_root = etree.fromstring(bytes(file.read(), encoding="utf-8"))

	acbf_tree = acbf_root.getroottree()
	acbf_schema = etree.XMLSchema(acbf_tree)

	if version == "1.0":
		try:
			acbf_schema.assertValid(tree)
		except etree.DocumentInvalid as err:
			warnings.warn("Validation failed. Books with 1.0 schema are not fully supported.", UserWarning)
			warnings.warn('Change the ACBF tag at the top of the `.acbf` XML file to `<ACBF xmlns="http://www.acbf.info/xml/acbf/1.1">` to use the 1.1 schema.', UserWarning)
			print(err)
	else:
		acbf_schema.assertValid(tree)

class ACBFBook:
	"""Base class for reading ACBF ebooks.

	Parameters
	----------
	file_path : str, default=Empty book template
		Path to ACBF book. May be absolute or relative.

	Raises
	------
	ValueError (File is not an ACBF Ebook.)
		Raised if the XML does not match ACBF schema or if archive does not contain ACBF file.

	See Also
	--------
	`ACBF Specifications <https://acbf.fandom.com/wiki/Advanced_Comic_Book_Format_Wiki>`_.

	Examples
	--------
	A book object can be opened, read and then closed. It can read files with the extensions
	``.acbf``, ``.cbz``, ``.cb7``, ``.cbt``, ``.cbr``. ::

		from libacbf import ACBFBook

		book = ACBFBook("path/to/file.cbz")
		# Read data from book
		book.close()

	``ACBFBook`` is also a context manager and can be used in with statements. ::

		from libacbf import ACBFBook

		with ACBFBook("path/to/file.cbz") as book:
			# Read data from book

	Attributes
	----------
	Metadata : ACBFMetadata
		See :class:`ACBFMetadata <libacbf.libacbf.ACBFMetadata>` for more information.

	Body : ACBFBody
		See :class:`ACBFBody <libacbf.libacbf.ACBFBody>` for more information.

	Data : ACBFData
		See :class:`ACBFData <libacbf.libacbf.ACBFData>` for more information.

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
		see :attr:`TextArea.paragraph <libacbf.body.TextArea.paragraph>`.

	Styles : dict-like object
		Get styles linked in the ACBF file.

		An object that behaves like a dictionary. Use ``Styles[file name]`` to get the contents of
		the stylesheet as a string. Use ``list_styles()`` to get list of all available styles. All
		paths are relative. ::

			style = book.Styles["style_name.css"]

		If a style is embedded in the ACBF file, use ``Styles["_"]`` to get its contents. ::

			embedded_stylesheet = book.Styles["_"]

	file_path : str
		Absolute path to source file.

	archive : ArchiveReader, optional
		Can be used to read archive directly if file is not ``.acbf``. There probably wont be any
		reason to use this.

		:attr:`ArchiveReader.archive <libacbf.archivereader.ArchiveReader.archive>` may be
		``zipfile.ZipFile``, ``py7zr.SevenZipFile``, ``tarfile.TarFile`` or ``rarfile.RarFile``.
	"""
	def __init__(self, file: Union[str, PurePath, IO] = "libacbf/templates/base_template_1.1.acbf"):
		if file == "libacbf/templates/base_template_1.1.acbf":
			raise NotImplementedError("Create new books TBD")

		self.is_open: bool = True

		self.book_path = None
		if isinstance(file, str):
			self.book_path = PurePath(os.path.abspath(file))
		if isinstance(file, PurePath):
			self.book_path = file

		self.archive: Optional[ArchiveReader] = None

		contents = None
		if not is_book_text(file):
			self.archive = ArchiveReader(file)
			contents = self.archive._get_acbf_contents()
		else:
			if self.book_path is None:
				if isinstance(file, TextIOBase):
					contents = file.read()
				else:
					contents = str(file.read(), encoding="utf-8")
			else:
				with open(file, encoding="utf-8") as book:
					contents = book.read()

		self._root = etree.fromstring(bytes(contents, encoding="utf-8"))

		self.namespace: str = r"{" + self._root.nsmap[None] + r"}"

		_validate_acbf(self._root, self.namespace)

		self.Styles: Styles = Styles(self, contents)

		self.Metadata: ACBFMetadata = ACBFMetadata(self)

		self.Body: ACBFBody = ACBFBody(self)

		self.Data: ACBFData = ACBFData(self)

		self.sync_references()

	def save(self, path: str = "", overwrite: bool = False):
		"""Save as file.

		Parameters
		----------
		path : str, optional
			Path to save to.
		overwrite : bool, optional
			Whether to overwrite if file already exists at path. ``False`` by default.

		Raises
		------
		NotImplementedError
			To do when making editor.py
		"""
		if path == "":
			path = self.book_path
		raise NotImplementedError

	def close(self):
		"""Closes open archives if file is ``.cbz``, ``.cbt`` or ``.cbr``. Removes temporary
		directory for ``.cb7`` files.
		"""
		if self.archive is not None:
			self.archive.close()
			self.is_open = False

	def sync_references(self):
		ns = self.namespace
		ref_root = self._root.find(f"{ns}references")
		references = {}
		if ref_root is not None:
			reference_items = ref_root.findall(f"{ns}reference")
			for ref in reference_items:
				pa = []
				for p in ref.findall(f"{ns}p"):
					text = re.sub(r"<\/?p[^>]*>", "", str(etree.tostring(p, encoding="utf-8"), encoding="utf-8").strip())
					pa.append(text)
				references[ref.attrib["id"]] = {"paragraph": "\n".join(pa)}
		self.References: Dict[str, Dict[str, str]] = references

	def __enter__(self):
		return self

	def __exit__(self, exception_type, exception_value, traceback):
		self.close()

class ACBFMetadata:
	"""Class to read metadata of the book.

	See Also
	--------
	`Meta-data Section Definition <https://acbf.fandom.com/wiki/Meta-data_Section_Definition>`_.

	Attributes
	----------
	book : ACBFBook
		Book that this metadata belongs to.

	book_info : BookInfo
		See :class:`BookInfo <libacbf.metadata.BookInfo>`.

	publisher_info : PublishInfo
		See :class:`PublishInfo <libacbf.metadata.PublishInfo>`.

	document_info : DocumentInfo
		See :class:`DocumentInfo <libacbf.metadata.DocumentInfo>`.
	"""
	def __init__(self, book: ACBFBook):
		self.book = book
		ns = book.namespace
		meta_root = book._root.find(f"{ns}meta-data")

		self.book_info: BookInfo = BookInfo(meta_root.find(f"{ns}book-info"), book)
		self.publisher_info: PublishInfo = PublishInfo(meta_root.find(f"{ns}publish-info"), book)
		self.document_info: DocumentInfo = DocumentInfo(meta_root.find(f"{ns}document-info"), book)

class ACBFBody:
	"""Body section contains the definition of individual book pages, text layers, frames and jumps
	inside those pages.

	See Also
	--------
	`Body Section Definition <https://acbf.fandom.com/wiki/Body_Section_Definition>`_.

	Attributes
	----------
	book : ACBFBook
		Book that this body section belongs to.

	pages : List[Page]
		A list of :class:`Page <libacbf.body.Page>` objects in order.

	bgcolor : str, optional
		Defines a background colour for the whole book. Can be overridden by ``bgcolor`` in pages,
		text layers and text areas.
	"""
	def __init__(self, book: ACBFBook):
		self.book = book

		ns = book.namespace
		body = book._root.find(f"{ns}body")
		page_items = body.findall(f"{ns}page")

		pgs = []
		for pg in page_items:
			pgs.append(Page(pg, book))

		self.pages: List[Page] = pgs

		# Optional
		self.bgcolor: Optional[str] = None
		if "bgcolor" in body.keys():
			self.bgcolor = body.attrib["bgcolor"]

class ACBFData:
	"""Get any binary data embedded in the ACBF file.

	See Also
	--------
	`Data Section Definition <https://acbf.fandom.com/wiki/Data_Section_Definition>`_.

	Returns
	-------
	BookData
		A file as a :class:`BookData <libacbf.bookdata.BookData>` object.

	Raises
	------
	FileNotFoundError
		Raised if file is not found embedded in the ACBF file.

	Examples
	--------
	To get a file embedded in the ACBF file::

		from libacbf import ACBFBook

		with ACBFBook("path/to/book.cbz") as book:
			image = book.Data["image.png"]
			font = book.Data["font.ttf"]
	"""
	def __init__(self, book: ACBFBook):
		self._ns = book.namespace
		self.book: ACBFBook = book
		self._root = book._root
		self._base = book._root.find(f"{self._ns}data")
		self._data_elements = []

		self.files: Dict[str, Optional[BookData]] = {}

		self.sync_data()

	def list_files(self) -> List[str]:
		"""Returns a list of all the names of the files embedded in the ACBF file. May be images,
		fonts etc.

		Returns
		-------
		List[str]
			A list of file names.
		"""
		fl = []
		for i in self.files.keys():
			fl.append(str(i))
		return fl

	def sync_data(self):
		self._base = self._root.find(f"{self._ns}data")
		if self._base is not None:
			self._data_elements = self._base.findall(f"{self._ns}binary")
		for i in self._data_elements:
			self.files[i.attrib["id"]] = None

	def __len__(self):
		return len(self.files.keys())

	def __getitem__(self, key: str):
		if key in self.files.keys():
			if self.files[key] is not None:
				return self.files[key]
			else:
				for i in self._data_elements:
					if i.attrib["id"] == key:
						new_data = BookData(key, i.attrib["content-type"], i.text)
						self.files[key] = new_data
						return new_data
		else:
			raise FileNotFoundError
