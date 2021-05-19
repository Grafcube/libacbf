from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Optional
from pathlib import Path
import os
import distutils.util
import re
import magic
import requests
import langcodes
from lxml import etree

if TYPE_CHECKING:
	from libacbf import ACBFBook
import libacbf.structs as structs
from libacbf.constants import BookNamespace, ImageRefType, PageTransitions, TextAreas
from libacbf.archivereader import ArchiveReader
from libacbf.bookdata import BookData

url_pattern = r'(((ftp|http|https):\/\/)|(\/)|(..\/))(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?'

class Page:
	"""A page in the book.

	See Also
	--------
	`Page Definition <https://acbf.fandom.com/wiki/Body_Section_Definition#Page>`_.

	Attributes
	----------
	book : ACBFBook
		Book that this page belongs to.

	image_ref : str
		Reference to the image file. May be embedded in the ACBF file, in the ACBF archive, in an
		external archive, a local path or a URL.

	ref_type : ImageRefType(Enum)
		A value from :class:`ImageRefType <libacbf.constants.ImageRefType>` indicating the type of
		reference in :attr:`image_ref`.

	title : Dict[str, str], optional
		It is used to define beginning of chapters, sections of the book and can be used to create a
		table of contents.

		Keys are standard language codes or ``"_"`` if not defined. Values are titles as string.

	bgcolor : str, optional
		Defines the background colour for the page. Inherits from :attr:`ACBFBody.bgcolor <libacbf.libacbf.ACBFBody.bgcolor>`
		if ``None``.

	transition: PageTransitions(Enum), optional
		Defines the type of transition from the previous page to this one. Allowed values are in
		:class:`PageTransitions <libacbf.constants.PageTransitions>`.
	"""
	def __init__(self, page, book: ACBFBook, coverpage: bool = False):
		ns: BookNamespace = book.namespace
		self._page = page
		self._text_layers = None
		self._frames = None
		self._jumps = None
		self._image = None

		self.book = book

		# Sub
		self.image_ref: str = page.find(f"{ns.ACBFns}image").attrib["href"]

		ref_t = None
		if self.image_ref.startswith("#"):
			ref_t = ImageRefType.Embedded
			self._file_id = re.sub("#", "", self.image_ref)

		elif self.image_ref.startswith("zip:"):
			ref_t = ImageRefType.Archived
			ref_path = re.sub("zip:", "", self.image_ref)
			self._arch_path = Path(re.split("!", ref_path)[0])
			self._file_path = Path(re.split("!", ref_path)[1])
			self._file_id = self._file_path.name
			if not os.path.isabs(self._arch_path):
				self._arch_path = Path(os.path.abspath(str(self._arch_path)))

		elif re.fullmatch(url_pattern, self.image_ref, re.IGNORECASE):
			ref_t = ImageRefType.URL
			self._file_id = re.split("/", self.image_ref)[-1]

		else:
			if self.image_ref.startswith("file://"):
				self._file_path = Path(os.path.abspath(self.image_ref))
			else:
				self._file_path = Path(self.image_ref)

			if os.path.isabs(self.image_ref):
				ref_t = ImageRefType.Local
			else:
				if book.archive is not None:
					ref_t = ImageRefType.SelfArchived
				else:
					ref_t = ImageRefType.Local
					self._file_path = Path(book.file_path).parent/self._file_path

			self._file_id = self._file_path.name

		self.ref_type: ImageRefType = ref_t

		# Optional
		if not coverpage:
			self.bgcolor: Optional[str] = None
			if "bgcolor" in page.keys():
				self.bgcolor = page.attrib["bgcolor"]

			self.transition: Optional[PageTransitions] = None
			if "transition" in page.keys():
				self.transition = PageTransitions[page.attrib["transition"]]

		## Optional
		if not coverpage:
			self.title: Dict[str, str] = {}
			title_items = page.findall(f"{ns.ACBFns}title")
			for t in title_items:
				if "lang" in t.keys():
					self.title[t.attrib["lang"]] = t.text
				else:
					self.title["_"] = t.text

	@property
	def image(self) -> BookData:
		"""Gets the image data from the source.

		Returns
		-------
		BookData
			A :class:`BookData <libacbf.bookdata.BookData>` object.
		"""
		if self._image is None:
			if self.ref_type == ImageRefType.Embedded:
				self._image = self.book.Data[self._file_id]
				return self._image

			elif self.ref_type == ImageRefType.Archived:
				with ArchiveReader(self._arch_path) as ext_archive:
					contents = ext_archive.read(str(self._file_path))

			elif self.ref_type == ImageRefType.URL:
				response = requests.get(self.image_ref)
				contents = response.content

			else:
				if self.ref_type == ImageRefType.SelfArchived:
					contents = self.book.archive.read(str(self._file_path))
				elif self.ref_type == ImageRefType.Local:
					with open(str(self._file_path), "rb") as image:
						contents = image.read()

			contents_type = magic.from_buffer(contents, True)
			self._image = BookData(self._file_id, contents_type, contents)

		return self._image

	@property
	def text_layers(self) -> Dict[str, TextLayer]:
		"""Gets the textlayers for this page.

		See Also
		--------
		`Text Layers <https://acbf.fandom.com/wiki/Body_Section_Definition#Text-layer>`_.

		Returns
		-------
		Dict[str, TextLayer]
			A dictionary with keys being a standard language object and values being
			:class:`TextLayer` objects.
		"""
		if self._text_layers is None:
			item = self._page
			ns = self.book.namespace
			text_layers = {}
			textlayer_items = item.findall(f"{ns.ACBFns}text-layer")
			for lr in textlayer_items:
				new_lr = TextLayer(lr, ns)
				text_layers[new_lr.language] = new_lr
			self._text_layers = text_layers
		return self._text_layers

	@property
	def frames(self) -> List[structs.Frame]:
		"""Gets the frames on this page.

		See Also
		--------
		`Frame specifications <https://acbf.fandom.com/wiki/Body_Section_Definition#Frame>`_.

		Returns
		-------
		List[Frame]
			A list of :class:`Frame <libacbf.structs.Frame>` objects.
		"""
		if self._frames is None:
			item = self._page
			ns = self.book.namespace
			frames = []
			frame_items = item.findall(f"{ns.ACBFns}frame")
			for fr in frame_items:
				frame = structs.Frame(get_points(fr.attrib["points"]))
				if "bgcolor" in fr.keys():
					frame.bgcolor = fr.attrib["bgcolor"]
				frames.append(frame)
			self._frames = frames
		return self._frames

	@property
	def jumps(self) -> List[structs.Jump]:
		"""Gets the jumps on this page.

		See Also
		--------
		`Jump specifications <https://acbf.fandom.com/wiki/Body_Section_Definition#Jump>`_.

		Returns
		-------
		List[Jump]
			A list of :class:`Jump <libacbf.structs.Jump>` objects.
		"""
		if self._jumps is None:
			item = self._page
			ns = self.book.namespace
			jumps = []
			jump_items = item.findall(f"{ns.ACBFns}jump")
			for jp in jump_items:
				jump = structs.Jump(get_points(jp.attrib["points"]), int(jp.attrib["page"]))
				jumps.append(jump)
			self._jumps = jumps
		return self._jumps

class TextLayer:
	"""Defines a text layer drawn on a page.

	See Also
	--------
	`Text Layer specifications <https://acbf.fandom.com/wiki/Body_Section_Definition#Text-layer>`_.

	Attributes
	----------
	language : str
		A standard language code that defines the language of the text in this layer.

	text_areas : List[TextArea]
		A list of :class:`TextArea` objects in order (order matters for text-to-speech).

	bgcolor : str, optional
		Defines the background colour of the text areas or inherits from :attr:`Page.bgcolor` if ``None``.
	"""
	def __init__(self, layer, ns: BookNamespace):
		self.language: str = langcodes.standardize_tag(layer.attrib["lang"])

		self.bgcolor: Optional[str] = None
		if "bgcolor" in layer.keys():
			self.bgcolor = layer.attrib["bgcolor"]

		# Sub
		self.text_areas: List[TextArea] = []
		areas = layer.findall(f"{ns.ACBFns}text-area")
		for ar in areas:
			self.text_areas.append(TextArea(ar, ns))

class TextArea:
	"""Defines an area where text is drawn.

	See Also
	--------
	`Text Area specifications <https://acbf.fandom.com/wiki/Body_Section_Definition#Text-area>`_.

	Attributes
	----------
	points : List[2D Vectors]
		A list of named tuples with ``x`` and ``y`` values representing a 2-dimensional vector. Same
		as :attr:`Frame.points <libacbf.structs.Frame.points>`.

	paragraph : str
		A multiline string of what text to show in the are. Can have special tags for formatting.

		<strong>...</strong>
			Bold letters.

		<emphasis>...</emphasis>
			Italicised or cursive text.

		<strikethrough>...</strikethrough>
			Striked-through text.

		<sub>...</sub>
			Subscript text.

		<sup>...</sup>
			Superscript text.

		<a href=“...“>...</a>
			A link. Internal or external.

	bgcolor : str, optional
		Defines the background colour of the text area or inherits from :attr:`TextLayer.bgcolor` if ``None``.

	rotation : int, optional
		Defines the rotation of the text layer.

		Can be an integer from 0 to 360.

	type : TextAreas(Enum), optional
		The type of text area. Rendering can be changed based on type.

		Allowed values are defined in :class:`TextAreas <libacbf.constants.TextAreas>`.

	inverted : bool, optional
		Whether text is rendered with inverted colour.

	transparent : bool, optional
		Whether text is drawn.
	"""
	def __init__(self, area, ns: BookNamespace):
		self.points: List[structs.Vec2] = get_points(area.attrib["points"])

		self.paragraph: str = ""
		pa = []
		for p in area.findall(f"{ns.ACBFns}p"):
			text = re.sub(r"<\/?p[^>]*>", "", str(etree.tostring(p, encoding="utf-8"), encoding="utf-8").strip())
			pa.append(text)
		self.paragraph = "\n".join(pa)

		# Optional
		self.bgcolor: Optional[str] = None
		if "bgcolor" in area.keys():
			self.bgcolor = area.attrib["bgcolor"]

		self.rotation: Optional[int] = None
		if "text-rotation" in area.keys():
			rot = int(area.attrib["text-rotation"])
			if rot >= 0 and rot <= 360:
				self.rotation = rot
			else:
				raise ValueError("Rotation must be an integer from 0 to 360.")

		self.type: Optional[TextAreas] = None
		if "type" in area.keys():
			self.type = TextAreas[area.attrib["type"]]

		self.inverted: Optional[bool] = None
		if "inverted" in area.keys():
			self.inverted = bool(distutils.util.strtobool(area.attrib["inverted"]))

		self.transparent: Optional[bool] = None
		if "transparent" in area.keys():
			self.transparent = bool(distutils.util.strtobool(area.attrib["transparent"]))

def get_points(pts_str: str):
	pts = []
	pts_l = re.split(" ", pts_str)
	for pt in pts_l:
		ls = re.split(",", pt)
		pts.append(structs.Vec2(int(ls[0]), int(ls[1])))
	return pts