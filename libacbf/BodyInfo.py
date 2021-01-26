from collections import namedtuple
from re import split
from lxml import etree
from libacbf.Constants import PageTransitions, TextAreas

class Page:
	"""
	docstring
	"""
	def __init__(self):
		self.bg_color = None

		self.transition = PageTransitions.fade

		self.title = {}

		self.image_ref = ""

		self.text_layers = {}

		self.frames = []

		self.jumps = []

	def dict(self):
		return {
			"bg_color": self.bg_color,
			"transition": str(self.transition),
			"title": self.title,
			"image_ref": self.image_ref,
			"text_layers": self.text_layers,
			"frames": self.frames,
			"jumps": self.jumps
		}

class TextLayer:
	"""
	docstring
	"""
	def __init__(self, layer: etree._Element, ACBFns: str):
		self.language = layer.attrib["lang"]

		if "bgcolor" in layer.keys():
			self.bg_colour = layer.attrib["bgcolor"]

		self.text_areas = []
		areas = layer.findall(f"{ACBFns}text-area")
		for ar in areas:
			self.text_areas.append(TextArea(ar, ACBFns))

class TextArea:
	"""
	docstring
	"""
	def __init__(self, area: etree._Element, ACBFns: str):
		self.points = get_points(area.attrib["points"])

		self.paragraph = []
		for p in area.findall(f"{ACBFns}p"):
			self.paragraph.append(etree.tostring(p, encoding="utf-8"))

		# Optional
		self.bg_colour = None
		if "bgcolor" in area.keys():
			self.bg_colour = area.attrib["bgcolor"]

		self.rotation = 0
		if "text-rotation" in area.keys():
			self.rotation = area.attrib["text-rotation"]

		self.type = TextAreas.Speech
		if "type" in area.keys():
			self.rotation = area.attrib["type"]

		self.inverted = False
		if "inverted" in area.keys():
			self.rotation = area.attrib["inverted"]

		self.transparent = False
		if "transparent" in area.keys():
			self.rotation = area.attrib["transparent"]

def get_textlayers(item, ACBFns):
	text_layers = {}
	textlayer_items = item.findall(f"{ACBFns}text-layer")
	for lr in textlayer_items:
		new_lr = TextLayer(lr)
		text_layers[new_lr.language] = new_lr
	return text_layers

def get_frames(item, ACBFns):
	frames = []
	frame_items = item.findall(f"{ACBFns}frame")
	for fr in frame_items:
		pts = get_points(fr.attrib["points"])

		bg = None
		if "bgcolor" in fr.keys():
			bg = fr.attrib["bgcolor"]

		frame = {
			"points": pts,
			"bgcolor": bg
		}
		frames.append(frame)

	return frames

def get_jumps(item, ACBFns):
	jumps = []
	jump_items = item.findall(f"{ACBFns}jump")
	for jp in jump_items:
		pts = get_points(jp.attrib["points"])

		jump = {
			"page": jp.attrib["page"],
			"points": pts
		}
		jumps.append(jump)

	return jumps

def get_points(pts_str: str):
	pts = []
	pts_l = split(" ", pts_str)
	for pt in pts_l:
		ls = split(",", pt)
		vec2 = namedtuple("Vector2", "x y")
		pts.append( vec2( int(ls[0]), int(ls[1]) ) )
	return pts
