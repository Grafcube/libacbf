from collections import OrderedDict
from re import split

class BookInfo:
	"""
	docstring
	"""
	def __init__(self, info: dict):
		"""
		docstring
		"""

		self.authors = []
		if type(info["author"]) is OrderedDict:
			self.authors = [info["author"]]
		elif type(info["author"]) is list:
			self.authors = info["author"]

		self.book_title = OrderedDict()
		if type(info["book-title"]) is OrderedDict:
			if "@lang" in info["book-title"]:
				self.book_title[info["book-title"]["@lang"]] = info["book-title"]["#text"]
			else:
				self.book_title["_"] = info["book-title"]["#text"]
		elif type(info["book-title"]) is list:
			for title in info["book-title"]:
				self.book_title[title["@lang"]] = title["#text"]

		self.genres = []
		if type(info["genre"]) is OrderedDict:
			self.genres = [info["genre"]]
		elif type(info["genre"]) is list:
			self.genres = info["genre"]

		self.annotations = []
		p = ""
		if type(info["annotation"]) is OrderedDict:
			if type(info["annotation"]["p"]) is str:
				p = info["annotation"]["p"]
			elif type(info["annotation"]["p"]) is list:
				p = "\n".join(info["annotation"]["p"])
			if "@lang" in info["annotation"]:
				self.annotations[info["annotation"]["@lang"]] = p
			else:
				self.annotations["_"] = p
		elif type(info["annotation"]) is list:
			for item in info["annotation"]:
				if type(item["p"]) is str:
					p = item["p"]
				elif type(item["p"]) is list:
					p = "\n".join(item["p"])
				self.annotations.append({item["@lang"]: p})

		self.cover_page = None # TBD

		self.languages = None # TBD

		self.text_layer = None # TBD

		# Optional props
		self.characters = []
		if type(info["characters"]["name"]) is list:
			self.characters = info["characters"]["name"]
		elif type(info["characters"]["name"]) is str:
			self.characters = [info["characters"]["name"]]

		self.keywords = split(",|, ", info["keywords"])

		self.series = []
		if type(info["sequence"]) is list:
			self.series = [info["sequence"]]
		elif type(info["sequence"]) is OrderedDict:
			self.series = [info["sequence"]]

		self.content_rating = None # TBD

		self.database_ref = None # TBD
