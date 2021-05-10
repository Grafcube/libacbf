from __future__ import annotations
from libacbf.ArchiveReader import ArchiveReader
import os
from typing import TYPE_CHECKING, List, Dict, Optional

if TYPE_CHECKING:
	from libacbf.ACBFBook import ACBFBook

from distutils.util import strtobool
from collections import namedtuple
from pathlib import Path
from magic.magic import from_buffer
from re import IGNORECASE, fullmatch, split, sub
import requests
from langcodes import Language, standardize_tag
from lxml import etree
from libacbf.BookData import BookData
from libacbf.Constants import BookNamespace, ImageRefType, PageTransitions, TextAreas
import libacbf.Structs as structs

Vec2 = namedtuple("Vector2", "x y")
url_pattern = r'(((ftp|http|https):\/\/)|(\/)|(..\/))(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@!\-\/]))?'

class Page:
	"""
	docstring
	"""
	def __init__(self, page, book: ACBFBook):
		self._image: Optional[BookData] = None

		self.book = book

		ns: BookNamespace = book.namespace

		# Optional
		self.bg_color: Optional[str] = None
		if "bgcolor" in page.keys():
			self.bg_color = page.attrib["bgcolor"]

		self.transition: Optional[PageTransitions] = None
		if "transition" in page.keys():
			self.transition = PageTransitions[page.attrib["transition"]]

		# Sub
		self.image_ref: str = page.find(f"{ns.ACBFns}image").attrib["href"]

		ref_t = None
		self._image = None

		if self.image_ref.startswith("#"):
			self._file_id = sub("#", "", self.image_ref)
			ref_t = ImageRefType.Embedded

		elif self.image_ref.startswith("zip:"):
			ref_t = ImageRefType.Archived

			ref_path = sub("zip:", "", self.image_ref)
			self._arch_path = Path(split("!", ref_path)[0])
			self._file_path = Path(split("!", ref_path)[1])
			self._file_id = self._file_path.name
			if not os.path.isabs(self._arch_path):
				self._arch_path = Path(os.path.abspath(str(self._arch_path)))

		elif fullmatch(url_pattern, self.image_ref, IGNORECASE):
			self._file_id = split("/", self.image_ref)[-1]
			ref_t = ImageRefType.URL

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

		## Optional
		self.title: Dict[str, str] = {}
		title_items = page.findall(f"{ns.ACBFns}title")
		for t in title_items:
			if "lang" in t.keys():
				self.title[t.attrib["lang"]] = t.text
			else:
				self.title["_"] = t.text

		self.text_layers: Dict[str, TextLayer] = get_textlayers(page, ns)

		self.frames: List[structs.Frame] = get_frames(page, ns)

		self.jumps: List[structs.Jump] = get_jumps(page, ns)

	@property
	def image(self) -> Optional[BookData]:
		if self._image is None:
			if self.image_ref.startswith("#"):
				self._image = self.book.Data[self._file_id]
				return self._image

			elif self.image_ref.startswith("zip:"):
				with ArchiveReader(self._arch_path) as ext_archive:
					contents = ext_archive.read(str(self._file_path))

			elif fullmatch(url_pattern, self.image_ref, IGNORECASE):
				response = requests.get(self.image_ref)
				contents = response.content

			else:
				if self.ref_type == ImageRefType.SelfArchived:
					contents = self.book.archive.read(str(self._file_path))
				elif self.ref_type == ImageRefType.Local:
					with open(str(self._file_path), "rb") as image:
						contents = image.read()

			contents_type = from_buffer(contents, True)
			self._image = BookData(self._file_id, contents_type, contents)

		return self._image

class TextLayer:
	"""
	docstring
	"""
	def __init__(self, layer, ns: BookNamespace):
		self.language: Language = Language.get(standardize_tag(layer.attrib["lang"]))

		self.bg_color: Optional[str] = None
		if "bgcolor" in layer.keys():
			self.bg_color = layer.attrib["bgcolor"]

		# Sub
		self.text_areas: List[TextArea] = []
		areas = layer.findall(f"{ns.ACBFns}text-area")
		for ar in areas:
			self.text_areas.append(TextArea(ar, ns))

class TextArea:
	"""
	docstring
	"""
	def __init__(self, area, ns: BookNamespace):
		self.points: List[Vec2] = get_points(area.attrib["points"])

		self.paragraph: str = ""
		pa = []
		for p in area.findall(f"{ns.ACBFns}p"):
			text = sub(r"<\/?p[^>]*>", "", str(etree.tostring(p, encoding="utf-8"), encoding="utf-8").strip())
			pa.append(text)
		self.paragraph = "\n".join(pa)

		# Optional
		self.bg_color: Optional[str] = None
		if "bgcolor" in area.keys():
			self.bg_color = area.attrib["bgcolor"]

		self.rotation: Optional[int] = None
		if "text-rotation" in area.keys():
			rot = int(area.attrib["text-rotation"])
			if rot >= 0 and rot <= 360:
				self.rotation = rot
			else:
				raise ValueError("Rotation must be an integer from0 to 360.")

		self.type: Optional[TextAreas] = None
		if "type" in area.keys():
			self.type = TextAreas[area.attrib["type"]]

		self.inverted: Optional[bool] = None
		if "inverted" in area.keys():
			self.inverted = bool(strtobool(area.attrib["inverted"]))

		self.transparent: Optional[bool] = None
		if "transparent" in area.keys():
			self.transparent = bool(strtobool(area.attrib["transparent"]))

def get_textlayers(item, ns: BookNamespace):
	text_layers = {}
	textlayer_items = item.findall(f"{ns.ACBFns}text-layer")
	for lr in textlayer_items:
		new_lr = TextLayer(lr, ns)
		text_layers[new_lr.language] = new_lr
	return text_layers

def get_frames(item, ns: BookNamespace):
	frames = []
	frame_items = item.findall(f"{ns.ACBFns}frame")
	for fr in frame_items:
		frame = structs.Frame()
		frame.points = get_points(fr.attrib["points"])

		if "bgcolor" in fr.keys():
			frame.bgcolor = fr.attrib["bgcolor"]

		frames.append(frame)

	return frames

def get_jumps(item, ns: BookNamespace):
	jumps = []
	jump_items = item.findall(f"{ns.ACBFns}jump")
	for jp in jump_items:
		jump = structs.Jump()
		jump.points = get_points(jp.attrib["points"])
		jump.page = jp.attrib["page"]

		jumps.append(jump)

	return jumps

def get_points(pts_str: str):
	pts = []
	pts_l = split(" ", pts_str)
	for pt in pts_l:
		ls = split(",", pt)
		pts.append(Vec2(int(ls[0]), int(ls[1])))
	return pts
