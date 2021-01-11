from collections import OrderedDict
from re import split
from lxml.etree import _Element

class BookInfo:
	"""
	docstring
	"""
	def __init__(self, info):
		"""
		docstring
		"""

		ACBFns = r"{http://www.fictionbook-lib.org/xml/acbf/1.0}"

		self.authors = []
		author_tree = info.findall(f"{ACBFns}author")
		for au in author_tree:
			new_author = {
				"activity": None,
				"lang": None,
				"first-name": au.find(f"{ACBFns}first-name").text,
				"last-name": au.find(f"{ACBFns}last-name").text,
				"middle-name": None,
				"nickname": None,
				"home-page": None,
				"email": None
			}

			if "activity" in au.keys():
				new_author["activity"] = au.attrib["activity"]
			if "lang" in au.keys():
				new_author["lang"] = au.attrib["lang"]

			if au.find(f"{ACBFns}middle-name") is not None:
				new_author["middle-name"] = au.find(f"{ACBFns}middle-name").text
			if au.find(f"{ACBFns}nickname") is not None:
				new_author["nickname"] = au.find(f"{ACBFns}nickname").text
			if au.find(f"{ACBFns}home-page") is not None:
				new_author["home-page"] = au.find(f"{ACBFns}home-page").text
			if au.find(f"{ACBFns}email") is not None:
				new_author["email"] = au.find(f"{ACBFns}email").text

			self.authors.append(new_author)

		self.book_title = {}
		book_tree = info.findall(f"{ACBFns}book-title")
		for title in book_tree:
			if "lang" in title.keys():
				self.book_title[title.attrib["lang"]] = title.text
			else:
				self.book_title["_"] = title.text

		self.genres = []
		genre_tree = info.findall(f"{ACBFns}genre")
		for genre in genre_tree:
			new_genre = {
				"genre": genre.text,
				"match": None
			}

			if "match" in genre.keys():
				new_genre["match"] = genre.attrib["match"]

			self.genres.append(new_genre)

		self.annotations = []
		# p = ""
		# if type(info["annotation"]) is OrderedDict:
		# 	if type(info["annotation"]["p"]) is str:
		# 		p = info["annotation"]["p"]
		# 	elif type(info["annotation"]["p"]) is list:
		# 		p = "\n".join(info["annotation"]["p"])
		# 	if "@lang" in info["annotation"]:
		# 		self.annotations[info["annotation"]["@lang"]] = p
		# 	else:
		# 		self.annotations["_"] = p
		# elif type(info["annotation"]) is list:
		# 	for item in info["annotation"]:
		# 		if type(item["p"]) is str:
		# 			p = item["p"]
		# 		elif type(item["p"]) is list:
		# 			p = "\n".join(item["p"])
		# 		self.annotations.append({item["@lang"]: p})

		self.cover_page = None # TBD

		self.languages = None # TBD

		# Optional props
		self.characters = []
		# if type(info["characters"]["name"]) is list:
		# 	self.characters = info["characters"]["name"]
		# elif type(info["characters"]["name"]) is str:
		# 	self.characters = [info["characters"]["name"]]

		self.keywords = None#split(",|, ", info["keywords"])

		self.series = []
		# if type(info["sequence"]) is list:
		# 	self.series = [info["sequence"]]
		# elif type(info["sequence"]) is OrderedDict:
		# 	self.series = [info["sequence"]]

		self.content_rating = None # TBD

		self.database_ref = None # TBD
