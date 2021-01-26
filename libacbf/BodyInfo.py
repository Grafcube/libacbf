from collections import namedtuple
from re import split
from libacbf.Constants import PageTransitions, TextAreas

class Page:
	"""
	docstring
	"""
	def __init__(self):
		self.bg_colour = None

		self.transition = PageTransitions.fade

		self.title = {}

		self.image_ref = ""

		self.text_layers = {}

		self.frames = [{
			"points": [()],
			"bgcolor": None
		}]

		self.jumps = [{
			"page": 0,
			"points": [()]
		}]

class TextLayer:
	"""
	docstring
	"""
	def __init__(self):
		self.language = ""

		self.points = [()]

		self.text = ""

		# Optional
		self.bg_colour = None

		self.rotation = 0

		self.type = TextAreas.Speech

		self.inverted = False

		self.transparent = False

		self.paragraph = ""

def get_textlayers(item, ACBFns):
	textlayer_items = item.findall(f"{ACBFns}text-layer")
	for lr in textlayer_items:
		pass

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

	if len(frames) > 1 or len(frames) == 0:
		return frames
	else:
		return frames[0]

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

	if len(jumps) > 1 or len(jumps) == 0:
		return jumps
	else:
		return jumps[0]

def get_points(pts_str: str):
	pts = split(pts_str)
	for pt in pts_str:
		ls = split(",", pt)
		pts.append(namedtuple((int(ls[0]), int(ls[1])), "x y"))
	return pts
