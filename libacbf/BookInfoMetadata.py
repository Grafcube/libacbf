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
		author_items = info.findall(f"{ACBFns}author")
		for au in author_items:
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
		book_items = info.findall(f"{ACBFns}book-title")
		for title in book_items:
			if "lang" in title.keys():
				self.book_title[title.attrib["lang"]] = title.text
			else:
				self.book_title["_"] = title.text

		self.genres = []
		genre_items = info.findall(f"{ACBFns}genre")
		for genre in genre_items:
			new_genre = {
				"genre": genre.text,
				"match": None
			}

			if "match" in genre.keys():
				new_genre["match"] = genre.attrib["match"]

			self.genres.append(new_genre)

		self.annotations = {}
		annotation_items = info.findall(f"{ACBFns}annotation")
		for an in annotation_items:
			p = []
			for i in an.findall(f"{ACBFns}p"):
				p.append(i.text)
			p = "\n".join(p)

			if "lang" in an.keys():
				self.annotations[an.attrib["lang"]] = p
			else:
				self.annotations["_"] = p

		self.cover_page = None # TBD

		self.languages = None # TBD

		# Optional props
		self.characters = []
		character_item = info.find(f"{ACBFns}characters")
		for c in character_item.findall(f"{ACBFns}name"):
			self.characters.append(c.text)

		self.keywords = []
		keyword_items = info.findall(f"{ACBFns}keywords")
		for k in keyword_items:
			new_k = {}
			if "lang" in k.keys():
				new_k[k.attrib["lang"]] = split(", |,", k.text)
			else:
				new_k["_"] = split(", |,", k.text)

			self.keywords.append(new_k)

		self.series = {}
		series_items = info.findall(f"{ACBFns}sequence")
		for se in series_items:
			new_se = {
				"volume": None,
				"lang": None,
				"sequence": se.text
			}
			if "volume" in se.keys():
				new_se["volume"] = se.attrib["volume"]
			if "lang" in se.keys():
				new_se["lang"] = se.attrib["lang"]

			self.series[se.attrib["title"]] = new_se

		self.content_rating = None # TBD

		self.database_ref = None # TBD
