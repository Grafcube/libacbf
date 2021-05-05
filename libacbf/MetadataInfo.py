from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Literal, Optional, Union
if TYPE_CHECKING:
	from libacbf.ACBFBook import ACBFBook

from distutils.util import strtobool
from re import split
from datetime import date
from langcodes import Language, standardize_tag
from libacbf.Constants import BookNamespace, Genres
from libacbf.Structs import Author, DBRef, Genre, CoverPage, LanguageLayer, Series
from libacbf.BodyInfo import get_textlayers, get_frames, get_jumps

class BookInfo:
	"""
	docstring
	"""
	def __init__(self, info, book: ACBFBook):
		self._info = info
		self._ns: BookNamespace = book.namespace

		self.sync_authors()
		self.sync_book_titles()
		self.sync_genres()
		self.sync_annotations()
		self.sync_coverpage()

		# Optional
		self.sync_languages()
		self.sync_characters()
		self.sync_keywords()
		self.sync_series()
		self.sync_content_rating()
		self.sync_database_ref()

	#region Sync
	def sync_authors(self):
		self.authors: List[Author] = update_authors(self._info.findall(f"{self._ns.ACBFns}author"), self._ns)

	def sync_book_titles(self):
		self._book_title: Dict[Union[Literal["_"], Language], str] = {}

		book_items = self._info.findall(f"{self._ns.ACBFns}book-title")
		for title in book_items:
			if "lang" in title.keys():
				lang = Language.get(standardize_tag(title.attrib["lang"]))
				self._book_title[lang] = title.text
			else:
				self._book_title["_"] = title.text

	def sync_genres(self):
		self._genres: Dict[str, Genre] = {}

		genre_items = self._info.findall(f"{self._ns.ACBFns}genre")
		for genre in genre_items:
			new_genre = Genre(genre.text)

			if "match" in genre.keys():
				new_genre.Match = int(genre.attrib["match"])

			self._genres[new_genre.Genre.name] = new_genre

	def sync_annotations(self):
		self._annotations: Dict[Union[Literal["_"], Language], str] = {}

		annotation_items = self._info.findall(f"{self._ns.ACBFns}annotation")
		for an in annotation_items:
			p = []
			for i in an.findall(f"{self._ns.ACBFns}p"):
				p.append(i.text)
			p = "\n".join(p)

			if "lang" in an.keys():
				lang = Language.get(standardize_tag(an.attrib["lang"]))
				self._annotations[lang] = p
			else:
				self._annotations["_"] = p

	def sync_coverpage(self):
		cpage = self._info.find(f"{self._ns.ACBFns}coverpage")
		self.cover_page: CoverPage = CoverPage(cpage.find(f"{self._ns.ACBFns}image").attrib["href"])
		self.cover_page.text_layers = get_textlayers(cpage, self._ns)
		self.cover_page.frames = get_frames(cpage, self._ns)
		self.cover_page.jumps = get_jumps(cpage, self._ns)

	def sync_languages(self):
		self.languages: List[LanguageLayer] = []

		if self._info.find(f"{self._ns.ACBFns}languages") is not None:
			text_layers = self._info.find(f"{self._ns.ACBFns}languages").findall(f"{self._ns.ACBFns}text-layer")
			for layer in text_layers:
				new_lang = LanguageLayer()

				new_lang.lang = layer.attrib["lang"]
				if "show" in layer.keys():
					new_lang.show = bool(strtobool(layer.attrib["show"]))

				self.languages.append(new_lang)

	def sync_characters(self):
		self.characters: List[str] = []

		character_item = self._info.find(f"{self._ns.ACBFns}characters")
		if character_item is not None:
			for c in character_item.findall(f"{self._ns.ACBFns}name"):
				self.characters.append(c.text)

	def sync_keywords(self):
		self.keywords: Dict[Union[Literal["_"], Language], List[str]] = {}

		keyword_items = self._info.findall(f"{self._ns.ACBFns}keywords")
		for k in keyword_items:
			if "lang" in k.keys():
				lang = Language.get(standardize_tag(k.attrib["lang"]))
				self.keywords[lang] = split(", |,", k.text)
			else:
				if k.text is not None:
					self.keywords["_"] = split(", |,", k.text)

	def sync_series(self):
		self.series: Dict[str, Series] = {}

		series_items = self._info.findall(f"{self._ns.ACBFns}sequence")
		for se in series_items:
			new_se = Series()
			new_se.title = se.attrib["title"]
			new_se.sequence = se.text

			if "volume" in se.keys():
				new_se.volume = se.attrib["volume"]
			if "lang" in se.keys():
				new_se.lang = se.attrib["lang"]

			self.series[se.attrib["title"]] = new_se

	def sync_content_rating(self):
		self.content_rating: Dict[str, str] = {}

		rating_items = self._info.findall(f"{self._ns.ACBFns}content-rating")
		for rt in rating_items:
			if "type" in rt.keys():
				self.content_rating[rt.attrib["type"]] = rt.text
			else:
				self.content_rating["_"] = rt.text

	def sync_database_ref(self):
		self.database_ref: List[DBRef] = []

		db_items = self._info.findall(f"{self._ns.ACBFns}databaseref")
		for db in db_items:
			new_db = DBRef()
			new_db.dbname = db.attrib["dbname"]
			new_db.text = db.text

			if "type" in db.keys():
				new_db.type = db.attrib["type"]

			self.database_ref.append(new_db)
	#endregion

	@property
	def book_title(self) -> Dict[Union[str, Language], str]:
		return self._book_title

	@book_title.setter
	def book_title(self, val: Dict[Union[str, Language], str]):
		pass

	def add_title(self, tt: str, lang: Union[str, Language] = "_"):
		pass

	def remove_title(self, idx: int):
		pass

	@property
	def genres(self) -> Dict[str, Genre]:
		return self._genres

	@genres.setter
	def genres(self, val: Dict[str, Genre]):
		pass

	def add_genre(self, gn: Genres, match: Optional[int] = None):
		pass

	def remove_genre(self, idx: int):
		pass

	@property
	def annotations(self) -> Dict[Union[str, Language], str]:
		return self._annotations

	@annotations.setter
	def annotations(self, val: Dict[Union[str, Language], str]):
		pass

	def add_annotation(self, an: str, lang: Union[str, Language] = "_"):
		pass

	def remove_annotation(self, idx: int):
		pass

	# Coverpage

	# Languages

	# Characters

	# Keywords

	# Series

	# Content Rating

	# Database Ref

class PublishInfo:
	"""
	docstring
	"""
	def __init__(self, info, book: ACBFBook):
		ns = book.namespace

		self.publisher: str = info.find(f"{ns.ACBFns}publisher").text

		self.publish_date_string: str = info.find(f"{ns.ACBFns}publish-date").text

		# Optional
		self.publish_date: Optional[date] = None
		if "value" in info.find(f"{ns.ACBFns}publish-date").keys():
			self.publish_date = date.fromisoformat(info.find(f"{ns.ACBFns}publish-date").attrib["value"])

		self.publish_city: Optional[str] = None
		if info.find(f"{ns.ACBFns}city") is not None:
			self.publish_city = info.find(f"{ns.ACBFns}city").text

		self.isbn: Optional[str] = None
		if info.find(f"{ns.ACBFns}isbn") is not None:
			self.isbn = info.find(f"{ns.ACBFns}isbn").text

		self.license: Optional[str] = None
		if info.find(f"{ns.ACBFns}license") is not None:
			self.license = info.find(f"{ns.ACBFns}license").text

class DocumentInfo:
	"""
	docstring
	"""
	def __init__(self, info, book: ACBFBook):
		ns: BookNamespace = book.namespace

		self.authors: List[Author] = update_authors(info.findall(f"{ns.ACBFns}author"), ns)

		self.creation_date_string: str = info.find(f"{ns.ACBFns}creation-date").text

		# Optional
		self.creation_date: Optional[date] = None
		if "value" in info.find(f"{ns.ACBFns}creation-date").keys():
			self.creation_date = date.fromisoformat(info.find(f"{ns.ACBFns}creation-date").attrib["value"])

		self.source: Optional[str] = None
		if info.find(f"{ns.ACBFns}source") is not None:
			p = []
			for line in info.findall(f"{ns.ACBFns}source/{ns.ACBFns}p"):
				p.append(line.text)
			self.source = "\n".join(p)

		self.document_id: Optional[str] = None
		if info.find(f"{ns.ACBFns}id") is not None:
			self.document_id = info.find(f"{ns.ACBFns}id").text

		self.document_version: Optional[str] = None
		if info.find(f"{ns.ACBFns}version") is not None:
			self.document_version = info.find(f"{ns.ACBFns}version").text

		self.document_history: List[str] = []
		if info.find(f"{ns.ACBFns}history") is not None:
			for item in info.findall(f"{ns.ACBFns}history/{ns.ACBFns}p"):
				self.document_history.append(item.text)

def update_authors(author_items, ns: BookNamespace):
	"""
	docstring
	"""
	authors = []

	for au in author_items:
		new_first_name = None
		new_last_name = None
		new_nickname = None
		if au.find(f"{ns.ACBFns}first-name") is not None:
			new_first_name = au.find(f"{ns.ACBFns}first-name").text
		if au.find(f"{ns.ACBFns}last-name") is not None:
			new_last_name = au.find(f"{ns.ACBFns}last-name").text
		if au.find(f"{ns.ACBFns}nickname") is not None:
			new_nickname = au.find(f"{ns.ACBFns}nickname").text

		new_author: Author = Author(new_first_name, new_last_name, new_nickname)
		new_author._element = au

		if "activity" in au.keys():
			new_author.activity = au.attrib["activity"]
		if "lang" in au.keys():
			new_author.lang = au.attrib["lang"]

		# Optional
		if au.find(f"{ns.ACBFns}middle-name") is not None:
			new_author.middle_name = au.find(f"{ns.ACBFns}middle-name").text
		if au.find(f"{ns.ACBFns}home-page") is not None:
			new_author.home_page = au.find(f"{ns.ACBFns}home-page").text
		if au.find(f"{ns.ACBFns}email") is not None:
			new_author.email = au.find(f"{ns.ACBFns}email").text

		authors.append(new_author)

	return authors
