from re import split
from datetime import date

class BookInfo:
	"""
	docstring
	"""
	def __init__(self, info, ACBFns):
		"""
		docstring
		"""
		self.authors = get_authors(info.findall(f"{ACBFns}author"), ACBFns)

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

		# Optional
		self.characters = []

		character_item = info.find(f"{ACBFns}characters")
		if type(character_item) is not None:
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

class PublishInfo:
	"""
	docstring
	"""
	def __init__(self, info: dict, ACBFns):
		"""
		docstring
		"""
		self.publisher = info.find(f"{ACBFns}publisher").text

		self.publish_date_string = info.find(f"{ACBFns}publish-date").text

		# Optional
		if "value" in info.find(f"{ACBFns}publish-date").keys():
			self.publish_date = date.fromisoformat(info.find(f"{ACBFns}publish-date").attrib["value"])

		self.publish_city = ""
		if type(info.find(f"{ACBFns}city")) is not None:
			self.publish_city = info.find(f"{ACBFns}city").text

		self.isbn = ""
		if type(info.find(f"{ACBFns}isbn")) is not None:
			self.isbn = info.find(f"{ACBFns}isbn").text

		self.license = ""
		if type(info.find(f"{ACBFns}license")) is not None:
			self.license = info.find(f"{ACBFns}license").text

class DocumentInfo:
	"""
	docstring
	"""
	def __init__(self, info: dict, ACBFns):
		"""
		docstring
		"""
		print(info.findall(f"{ACBFns}author"))
		self.authors = get_authors(info.findall(f"{ACBFns}author"), ACBFns)

		self.creation_date_string = info.find(f"{ACBFns}creation-date").text

		# Optional
		if "value" in info.find(f"{ACBFns}creation-date").keys():
			self.creation_date = date.fromisoformat(info.find(f"{ACBFns}creation-date").attrib["value"])

		p = []
		for line in info.findall(f"{ACBFns}source/{ACBFns}p"):
			p.append(line.text)
		self.source = "\n".join(p)

		self.document_id = ""
		if type(info.find(f"{ACBFns}id")) is not None:
			self.document_id = info.find(f"{ACBFns}id").text

		self.document_version = ""
		if type(info.find(f"{ACBFns}version")) is not None:
			self.document_version = info.find(f"{ACBFns}version").text

		self.document_history = []
		if type(info.find(f"{ACBFns}history")) is not None:
			for item in info.findall(f"{ACBFns}history/{ACBFns}p"):
				self.document_history.append(item.text)

def get_authors(author_items, ACBFns):
	"""
	docstring
	"""
	authors = []

	for au in author_items:
		new_author = {
			"activity": None,
			"lang": None,
			"first-name": None,
			"last-name": None,
			"middle-name": None,
			"nickname": None,
			"home-page": None,
			"email": None
		}

		if "activity" in au.keys():
			new_author["activity"] = au.attrib["activity"]
		if "lang" in au.keys():
			new_author["lang"] = au.attrib["lang"]

		if (au.find(f"{ACBFns}first-name") is not None and au.find(f"{ACBFns}last-name") is not None) or au.find(f"{ACBFns}nickname") is not None:
			if au.find(f"{ACBFns}first-name") is not None:
				new_author["first-name"] = au.find(f"{ACBFns}first-name").text
			if au.find(f"{ACBFns}last-name") is not None:
				new_author["last-name"] = au.find(f"{ACBFns}last-name").text
			if au.find(f"{ACBFns}nickname") is not None:
				new_author["nickname"] = au.find(f"{ACBFns}nickname").text
		else:
			raise ValueError("Author must have either First Name and Last Name or Nickname")

		# Optional
		if au.find(f"{ACBFns}middle-name") is not None:
			new_author["middle-name"] = au.find(f"{ACBFns}middle-name").text
		if au.find(f"{ACBFns}home-page") is not None:
			new_author["home-page"] = au.find(f"{ACBFns}home-page").text
		if au.find(f"{ACBFns}email") is not None:
			new_author["email"] = au.find(f"{ACBFns}email").text

		authors.append(new_author)

	return authors
