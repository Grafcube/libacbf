from collections import OrderedDict
from re import split
from lxml import etree

class BookInfo:
	"""
	docstring
	"""
	def __init__(self, info: etree._Element):
		"""
		docstring
		"""

		ACBFns = r"{http://www.fictionbook-lib.org/xml/acbf/1.0}"

		self.authors = []
		author_tree = info.findall(f"{ACBFns}author")
		for au in author_tree:
			self.authors.append({
				"activity": None,
				"lang": None,
				"first-name": au.find(f"{ACBFns}first-name"),
				"last-name": au.find(f"{ACBFns}last-name"),
				"middle-name": None,
				"nickname": None,
				"home-page": None,
				"email": None
			})

			if "activity" in au.keys():
				self.authors[-1]["activity"] = au.attrib["activity"]
			if "lang" in au.keys():
				self.authors[-1]["lang"] = au.attrib["lang"]

			if au.find(f"{ACBFns}middle-name") is not None:
				self.authors[-1]["middle-name"] = au.find(f"{ACBFns}middle-name")
			if au.find(f"{ACBFns}nickname") is not None:
				self.authors[-1]["nickname"] = au.find(f"{ACBFns}nickname")
			if au.find(f"{ACBFns}home-page") is not None:
				self.authors[-1]["home-page"] = au.find(f"{ACBFns}home-page")
			if au.find(f"{ACBFns}email") is not None:
				self.authors[-1]["email"] = au.find(f"{ACBFns}email")

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
