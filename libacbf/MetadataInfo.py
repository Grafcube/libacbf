from re import split
from datetime import date
from typing import AnyStr, Dict, List, Optional
from libacbf.ACBFBook import BookNamespace
from libacbf.Structs import Author, DBRef, Genre, CoverPage, LanguageLayer, Series
from libacbf.BodyInfo import TextArea, get_textlayers, get_frames, get_jumps

class BookInfo:
	"""
	docstring
	"""
	def __init__(self, info, ns: BookNamespace):
		self.authors: List[Author] = get_authors(info.findall(f"{ns.ACBFns}author"), ns)

		self.book_title: Dict[AnyStr, AnyStr] = {}

		book_items = info.findall(f"{ns.ACBFns}book-title")
		for title in book_items:
			if "lang" in title.keys():
				self.book_title[title.attrib["lang"]] = title.text
			else:
				self.book_title["_"] = title.text

		self.genres: List[Genre] = []

		genre_items = info.findall(f"{ns.ACBFns}genre")
		for genre in genre_items:
			new_genre = Genre()
			new_genre.Genre = genre.text

			if "match" in genre.keys():
				new_genre.Match = int(genre.attrib["match"])

			self.genres.append(new_genre)

		self.annotations: Dict[AnyStr, AnyStr] = {}

		annotation_items = info.findall(f"{ns.ACBFns}annotation")
		for an in annotation_items:
			p = []
			for i in an.findall(f"{ns.ACBFns}p"):
				p.append(i.text)
			p = "\n".join(p)

			if "lang" in an.keys():
				self.annotations[an.attrib["lang"]] = p
			else:
				self.annotations["_"] = p

		self.cover_page: CoverPage = CoverPage()
		coverpage_item = info.find(f"{ns.ACBFns}coverpage")
		self.cover_page.image_ref = coverpage_item.find(f"{ns.ACBFns}image").attrib["href"]
		self.cover_page.text_layers = get_textlayers(coverpage_item, ns)
		self.cover_page.frames = get_frames(coverpage_item, ns)
		self.cover_page.jumps = get_jumps(coverpage_item, ns)

		# Optional
		self.languages: List[LanguageLayer] = []

		if info.find(f"{ns.ACBFns}languages") is not None:
			text_layers = info.find(f"{ns.ACBFns}languages").findall(f"{ns.ACBFns}text-layer")
			for layer in text_layers:
				new_lang = LanguageLayer()

				new_lang.lang = layer.attrib["lang"]
				if "show" in title.keys():
					new_lang.show = layer.attrib["show"]

				self.languages.append(new_lang)

		self.characters: List[AnyStr] = []

		character_item = info.find(f"{ns.ACBFns}characters")
		if character_item is not None:
			for c in character_item.findall(f"{ns.ACBFns}name"):
				self.characters.append(c.text)

		self.keywords: List[Dict[AnyStr, List[AnyStr]]] = []

		keyword_items = info.findall(f"{ns.ACBFns}keywords")
		for k in keyword_items:
			new_k = {}
			if "lang" in k.keys():
				new_k[k.attrib["lang"]] = split(", |,", k.text)
			else:
				if k.text is not None:
					new_k["_"] = split(r", |,", k.text)

			self.keywords.append(new_k)

		self.series: Dict[AnyStr, Series] = {}

		series_items = info.findall(f"{ns.ACBFns}sequence")
		for se in series_items:
			new_se = Series()
			new_se.title = se.attrib["title"]
			new_se.sequence = se.text

			if "volume" in se.keys():
				new_se.volume = se.attrib["volume"]
			if "lang" in se.keys():
				new_se.lang = se.attrib["lang"]

			self.series[se.attrib["title"]] = new_se

		self.content_rating: Dict[AnyStr, AnyStr] = {}

		rating_items = info.findall(f"{ns.ACBFns}content-rating")
		for rt in rating_items:
			if "type" in rt.keys():
				self.content_rating[rt.attrib["type"]] = rt.text
			else:
				self.content_rating["_"] = rt.text

		self.database_ref: List[DBRef] = []

		db_items = info.findall(f"{ns.ACBFns}databaseref")
		for db in db_items:
			new_db = DBRef()
			new_db.dbname = db.attrib["dbname"]
			new_db.text = db.text

			if "type" in db.keys():
				new_db.type = db.attrib["type"]

			self.database_ref.append(new_db)

class PublishInfo:
	"""
	docstring
	"""
	def __init__(self, info: dict, ns: BookNamespace):
		self.publisher: AnyStr = info.find(f"{ns.ACBFns}publisher").text

		self.publish_date_string: AnyStr = info.find(f"{ns.ACBFns}publish-date").text

		# Optional
		self.publish_date: Optional[date] = None
		if "value" in info.find(f"{ns.ACBFns}publish-date").keys():
			self.publish_date = date.fromisoformat(info.find(f"{ns.ACBFns}publish-date").attrib["value"])

		self.publish_city: Optional[AnyStr] = None
		if info.find(f"{ns.ACBFns}city") is not None:
			self.publish_city = info.find(f"{ns.ACBFns}city").text

		self.isbn: Optional[AnyStr] = None
		if info.find(f"{ns.ACBFns}isbn") is not None:
			self.isbn = info.find(f"{ns.ACBFns}isbn").text

		self.license: Optional[AnyStr] = None
		if info.find(f"{ns.ACBFns}license") is not None:
			self.license = info.find(f"{ns.ACBFns}license").text

class DocumentInfo:
	"""
	docstring
	"""
	def __init__(self, info: dict, ns: BookNamespace):
		self.authors: List[Author] = get_authors(info.findall(f"{ns.ACBFns}author"), ns)

		self.creation_date_string: AnyStr = info.find(f"{ns.ACBFns}creation-date").text

		# Optional
		self.creation_date: Optional[date] = None
		if "value" in info.find(f"{ns.ACBFns}creation-date").keys():
			self.creation_date = date.fromisoformat(info.find(f"{ns.ACBFns}creation-date").attrib["value"])

		self.source: Optional[AnyStr] = None
		if info.find(f"{ns.ACBFns}source") is not None:
			p = []
			for line in info.findall(f"{ns.ACBFns}source/{ns.ACBFns}p"):
				p.append(line.text)
			self.source = "\n".join(p)

		self.document_id: Optional[AnyStr] = None
		if info.find(f"{ns.ACBFns}id") is not None:
			self.document_id = info.find(f"{ns.ACBFns}id").text

		self.document_version: Optional[AnyStr] = None
		if info.find(f"{ns.ACBFns}version") is not None:
			self.document_version = info.find(f"{ns.ACBFns}version").text

		self.document_history: List[AnyStr] = []
		if info.find(f"{ns.ACBFns}history") is not None:
			for item in info.findall(f"{ns.ACBFns}history/{ns.ACBFns}p"):
				self.document_history.append(item.text)

def get_authors(author_items, ns: BookNamespace):
	"""
	docstring
	"""
	authors = []

	for au in author_items:
		new_author: Author = Author()

		if "activity" in au.keys():
			new_author.activity = au.attrib["activity"]
		if "lang" in au.keys():
			new_author.lang = au.attrib["lang"]

		if (au.find(f"{ns.ACBFns}first-name") is not None and au.find(f"{ns.ACBFns}last-name") is not None) or au.find(f"{ns.ACBFns}nickname") is not None:
			if au.find(f"{ns.ACBFns}first-name") is not None:
				new_author.first_name = au.find(f"{ns.ACBFns}first-name").text
			if au.find(f"{ns.ACBFns}last-name") is not None:
				new_author.last_name = au.find(f"{ns.ACBFns}last-name").text
			if au.find(f"{ns.ACBFns}nickname") is not None:
				new_author.nickname = au.find(f"{ns.ACBFns}nickname").text
		else:
			raise ValueError("Author must have either First Name and Last Name or Nickname")

		# Optional
		if au.find(f"{ns.ACBFns}middle-name") is not None:
			new_author.middle_name = au.find(f"{ns.ACBFns}middle-name").text
		if au.find(f"{ns.ACBFns}home-page") is not None:
			new_author.home_page = au.find(f"{ns.ACBFns}home-page").text
		if au.find(f"{ns.ACBFns}email") is not None:
			new_author.email = au.find(f"{ns.ACBFns}email").text

		authors.append(new_author)

	return authors
