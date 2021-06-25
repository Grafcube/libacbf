from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict, Optional, Tuple
import os
import distutils.util
import re
import magic
import requests
import langcodes
from pathlib import Path
from lxml import etree

if TYPE_CHECKING:
	from libacbf import ACBFBook
import libacbf.structs as structs
import libacbf.helpers as helpers
from libacbf.constants import ImageRefType, PageTransitions, TextAreas
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
		self.book = book
		self._ns = book._namespace
		self._page = page

		self._text_layers = None
		self._frames = None
		self._jumps = None

		self.is_coverpage: bool = coverpage

		# Sub
		self.sync_image_ref()

		# --- Optional ---
		if not coverpage:
			self.bgcolor: Optional[str] = None
			if "bgcolor" in page.keys():
				self.bgcolor = page.attrib["bgcolor"]

			self.transition: Optional[PageTransitions] = None
			if "transition" in page.keys():
				self.transition = PageTransitions[page.attrib["transition"]]

			self.title: Dict[str, str] = {}
			title_items = page.findall(f"{self._ns}title")
			for t in title_items:
				if "lang" in t.keys():
					self.title[langcodes.standardize_tag(t.attrib["lang"])] = t.text
				else:
					self.title['_'] = t.text

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
			self.text_layers = {}
			textlayer_items = item.findall(f"{self._ns}text-layer")
			for lr in textlayer_items:
				new_lr = TextLayer(lr, self._ns)
				self.text_layers[new_lr.language] = new_lr
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
			frames = []
			frame_items = item.findall(f"{self._ns}frame")
			for fr in frame_items:
				frame = structs.Frame(structs.pts_to_vec(fr.attrib["points"]))
				frame._element = fr
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
			jumps = []
			jump_items = item.findall(f"{self._ns}jump")
			for jp in jump_items:
				jump = structs.Jump(structs.pts_to_vec(jp.attrib["points"]), int(jp.attrib["page"]))
				jump._element = jp
				jumps.append(jump)
			self._jumps = jumps
		return self._jumps

	def sync_image_ref(self):
		self._image = None
		self.image_ref: str = self._page.find(f"{self._ns}image").attrib["href"]

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
				if self.book.archive is not None:
					ref_t = ImageRefType.SelfArchived
				else:
					ref_t = ImageRefType.Local
					self._file_path = self.book.book_path.parent/self._file_path

			self._file_id = self._file_path.name

		self.ref_type: ImageRefType = ref_t

	# Editor
	@helpers.check_book
	def set_image_ref(self, img_ref: str):
		self._page.find(f"{self._ns}image").set("href", img_ref)
		self.sync_image_ref()

	# --- Optional ---
	@helpers.check_book
	def set_bgcolor(self, bg: Optional[str]):
		if self.is_coverpage:
			raise AttributeError("`coverpage` has no attribute `bgcolor`.")

		if bg is not None:
			self._page.set("bgcolor", bg)
		elif "bgcolor" in self._page.attrib:
			self._page.attrib.pop("bgcolor")
		self.bgcolor = bg

	@helpers.check_book
	def set_transition(self, tr: Optional[PageTransitions]):
		if self.is_coverpage:
			raise AttributeError("`coverpage` has no attribute `transition`.")

		if tr is not None:
			self._page.set("transition", tr.name)
			self.transition = tr
		elif "transition" in self._page.attrib:
			self._page.attrib.pop("transition")
			self.transition = None

	@helpers.check_book
	def set_title(self, tl: Optional[str], lang: str = '_'):
		if self.is_coverpage:
			raise AttributeError("`coverpage` has no attribute `title`.")

		lang = langcodes.standardize_tag(lang) if lang != '_' else lang
		tl_items = self._page.findall(f"{self._ns}title")

		tl_element = None
		if lang == '_':
			for i in tl_items:
				if "lang" not in i.keys():
					tl_element = i
					break
		else:
			for i in tl_items:
				if langcodes.standardize_tag(i.attrib["lang"]) == lang:
					tl_element = i
					break

		if tl is not None:
			if tl_element is None:
				tl_element = etree.SubElement(self._page, f"{self._ns}title")
				if lang != '_':
					tl_element.set("lang", lang)
			tl_element.text = tl
			self.title[lang] = tl
		elif tl_element is not None:
			tl_element.clear()
			self._page.remove(tl_element)
			self.title[lang] = tl

	# Text Layers
	@helpers.check_book
	def add_textlayer(self, lang: str) -> TextLayer:
		lang = langcodes.standardize_tag(lang)
		t_layer = etree.SubElement(self._page, f"{self._ns}text-layer", {"lang": lang})
		self.text_layers[lang] = TextLayer(t_layer, self._ns)
		return self.text_layers[lang]

	@helpers.check_book
	def remove_textlayer(self, lang: str):
		t_layer = self.text_layers.pop(lang)
		t_layer._layer.clear()
		self._page.remove(t_layer._layer)

	@helpers.check_book
	def change_textlayer_lang(self, src_lang: str, dest_lang: str):
		src_lang, dest_lang = map(langcodes.standardize_tag, (src_lang, dest_lang))
		t_layer = self.text_layers.pop(src_lang)
		t_layer._layer.set("lang", dest_lang)
		t_layer.language = dest_lang
		self.text_layers[dest_lang] = t_layer

	# Frames
	@helpers.check_book
	def insert_new_frame(self, index: int, points: List[Tuple[int, int]]) -> structs.Frame:
		fr_element = etree.Element(f"{self._ns}frame", {"points": structs.vec_to_pts(points)})
		fr = structs.Frame([structs.Vec2(x, y) for x, y in points])
		fr._element = fr_element

		if index == len(self.frames):
			self.frames[-1]._element.addnext(fr_element)
			self.frames.append(fr)
		else:
			self.frames[index]._element.addprevious(fr_element)
			self.frames.insert(index, fr)
		return fr

	@helpers.check_book
	def remove_frame(self, index: int):
		fr = self.frames.pop(index)
		fr._element.clear()
		self._page.remove(fr._element)

	@helpers.check_book
	def reorder_frame(self, src_index: int, dest_index: int):
		fr = self.frames.pop(src_index)
		if dest_index == len(self.frames):
			self._page.remove(fr._element)
			self.frames[-1]._element.addnext(fr._element)
		else:
			self.frames[dest_index] # Checks if index is in bounds before removing element
			self._page.remove(fr._element)
			self.frames[dest_index]._element.addprevious(fr._element)
		self.frames.insert(dest_index, fr)

	# Jumps
	@helpers.check_book
	def add_jump(self, target_page: int, points: List[Tuple[int, int]]) -> structs.Jump:
		jp_element = etree.SubElement(self._page, f"{self._ns}jump")
		jp_element.set("page", str(target_page))
		jp_element.set("points", structs.vec_to_pts(points))
		jp = structs.Jump([structs.Vec2(x, y) for x, y in points], target_page)
		jp._element = jp_element
		self.jumps.append(jp)
		return jp

	@helpers.check_book
	def remove_jump(self, index: int):
		jp = self.jumps.pop(index)
		jp._element.clear()
		self._page.remove(jp._element)

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
	def __init__(self, layer, ns):
		self._layer = layer
		self._ns = ns

		self.language: str = langcodes.standardize_tag(layer.attrib["lang"])

		self.bgcolor: Optional[str] = None
		if "bgcolor" in layer.keys():
			self.bgcolor = layer.attrib["bgcolor"]

		# Sub
		self.text_areas: List[TextArea] = []
		areas = layer.findall(f"{ns}text-area")
		for ar in areas:
			self.text_areas.append(TextArea(ar, ns))

	@helpers.check_book
	def set_bgcolor(self, bg: Optional[str]):
		if bg is not None:
			self._layer.set("bgcolor", bg)
		elif "bgcolor" in self._layer.attrib:
			self._layer.attrib.pop("bgcolor")
		self.bgcolor = bg

	@helpers.check_book
	def insert_new_textarea(self, idx: int, points: List[Tuple[int, int]], paragraph: str) -> TextArea:
		ta = etree.Element(f"{self._ns}text-area")
		ta.set("points", structs.vec_to_pts(points))
		ta.extend(structs.para_to_tree(paragraph, self._ns))
		self._layer.insert(idx, ta)
		self.text_areas.insert(idx, TextArea(ta, self._ns))
		return self.text_areas[idx]

	@helpers.check_book
	def remove_textarea(self, idx: int):
		ta = self.text_areas.pop(idx)
		ta._area.clear()
		self._layer.remove(ta._area)

	@helpers.check_book
	def reorder_textarea(self, src_index: int, dest_index: int):
		ta = self.text_areas.pop(src_index)
		self._layer.remove(ta._area)
		self._layer.insert(dest_index, ta._area)
		self.text_areas.insert(dest_index, ta)

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
	def __init__(self, area, ns):
		self._area = area
		self._ns = ns

		self.points: List[structs.Vec2] = structs.pts_to_vec(area.attrib["points"])

		self.paragraph: str = structs.tree_to_para(area, ns)

		# Optional
		self.bgcolor: Optional[str] = None
		if "bgcolor" in area.keys():
			self.bgcolor = area.attrib["bgcolor"]

		self.rotation: Optional[int] = None
		if "text-rotation" in area.keys():
			rot = int(area.attrib["text-rotation"])
			if 0 <= rot <= 360:
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

	# Editor
	@helpers.check_book
	def set_point(self, idx: int, x: int, y: int):
		self.points[idx] = structs.Vec2(x, y)
		self._area.set("points", structs.vec_to_pts(self.points))

	@helpers.check_book
	def remove_point(self, idx: int):
		if len(self.points) == 1:
			raise ValueError("`points` cannot be empty.")
		self.points.pop(idx)
		self._area.set("points", structs.vec_to_pts(self.points))

	@helpers.check_book
	def set_paragraph(self, paragraph: str):
		for i in self._area.iter():
			if i != self._area:
				i.clear()
				self._area.remove(i)
		self._area.extend(structs.para_to_tree(paragraph, self._ns))
		self.paragraph = paragraph

	# --- Optional ---
	@helpers.check_book
	def set_bgcolor(self, bg: Optional[str]):
		if bg is not None:
			self._area.set("bgcolor", bg)
		elif "bgcolor" in self._area.attrib:
			self._area.attrib.pop("bgcolor")
		self.bgcolor = bg

	@helpers.check_book
	def set_rotation(self, rot: Optional[int]):
		if rot is None:
			if "text-rotation" in self._area.keys():
				self._area.attrib.pop("text-rotation")
		elif 0 <= rot <= 360:
			self._area.set("text-rotation", str(rot))
		else:
			raise ValueError("Rotation must be an integer from 0 to 360.")
		self.rotation = rot

	@helpers.check_book
	def set_type(self, ty: Optional[TextAreas]):
		if ty is None:
			if "type" in self._area.keys():
				self._area.attrib.pop("type")
		else:
			self._area.set("type", ty.name)
		self.type = ty

	@helpers.check_book
	def set_inverted(self, inv: Optional[bool]):
		if inv is None:
			if "inverted" in self._area.keys():
				self._area.attrib.pop("inverted")
		else:
			self._area.set("inverted", str(inv).lower())
		self.inverted = inv

	@helpers.check_book
	def set_transparent(self, tra: Optional[bool]):
		if tra is None:
			if "transparent" in self._area.keys():
				self._area.attrib.pop("transparent")
		else:
			self._area.set("transparent", str(tra).lower())
		self.transparent = tra
