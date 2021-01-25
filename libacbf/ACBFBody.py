from libacbf.Constants import PageTransitions, TextAreas

class ACBFBody:
	"""
	docstring
	"""
	def __init__(self):
		self.pages = []

class Page:
	"""
	docstring
	"""
	def __init__(self):
		self.bg_colour = "#000000"

		self.transition = PageTransitions.fade

		self.title = {}

class Image:
	"""
	docstring
	"""
	def __init__(self):
		self.reference = ""

class TextLayer:
	"""
	docstring
	"""
	def __init__(self):
		self.points = []

		self.text = ""

		# Optional
		self.bg_colour = "#000000"

		self.rotation = 0

		self.type = TextAreas.Speech

		self.inverted = False

		self.transparent = False
