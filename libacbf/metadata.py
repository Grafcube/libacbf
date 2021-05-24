from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional
from datetime import date
import distutils.util
import re
import langcodes

if TYPE_CHECKING:
	from libacbf import ACBFBook
from libacbf.body import Page
from libacbf.structs import Author, DBRef, Genre, LanguageLayer, Series
from libacbf.constants import BookNamespace

class BookInfo:
	"""Metadata about the book itself.

	See Also
	--------
	`Book-Info section <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Book-info_section>`_.

	Attributes
	----------
	book : ACBFBook
		Book that the metadata belongs to.

	authors : List[Author]
		A list of :class:`Author <libacbf.structs.Author>` objects.

	book_titles : Dict[str, str]
		A dictionary with standard language codes as keys and titles as values. Key is ``"_"`` if no
		language is defined. ::

			{
				"_": "book title without language",
				"en": "English title",
				"en_GB": "English (UK) title",
				"en_US": "English (US) title"
			}

	genres : Dict[str, Genre]
		A dictionary with keys being a string representation of :class:`Genres <libacbf.constants.Genres>`
		Enum and values being :class:`Genre <libacbf.structs.Genre>` objects.

	annotations : Dict[str, str]
		A short summary describing the book.

		It is a dictionary with keys being standard language codes or ``"_"`` if no language is
		defined and values being multiline strings.

	cover_page : Page
		``cover_page`` is the same as :class:`Page <libacbf.body.Page>` except it does not have
		:attr:`title <libacbf.body.Page.title>`, :attr:`bgcolor <libacbf.body.Page.bgcolor>`
		and :attr:`transition <libacbf.body.Page.transition>`.

	languages : List[LanguageLayer], optional
		``LanguageLayer`` represents all :class:`TextLayer <libacbf.body.TextLayer>` objects of a language.

		A list of :class:`LanguageLayer <libacbf.structs.LanguageLayer>` objects.

	characters : List[str], optional
		List of (main) characters that appear in the book.

	keywords: Dict[str, List[str]], optional
		For use by search engines.

		A dictionary with keys as standard language codes or ``"_"`` if no language is defined.
		Values are a list of keywords.

	series: Dict[str, Series], optional
		Contains the sequence and number if particular comic book is part of a series.

		A dictionary with keys as the title of the series and values as :class:`Series <libacbf.structs.Series>`
		objects.

	content_rating: Dict[str, str], optional
		Content rating of the book based on age appropriateness and trigger warnings.

		It is a dictionary with the keys being the rating system or ``"_"`` if not defined and
		values being the rating itself. ::

			{
				"_": "18+"
			}

	database_ref : List[DBRef], optional
		Contains reference to a record in a comic book database (eg: GCD, MAL).

		A list of :class:`DBRef <libacbf.structs.DBRef>` objects.
	"""
	def __init__(self, info, book: ACBFBook):
		self.book = book
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
		self.book_title: Dict[str, str] = {}

		book_items = self._info.findall(f"{self._ns.ACBFns}book-title")
		for title in book_items:
			if "lang" in title.keys():
				lang = langcodes.standardize_tag(title.attrib["lang"])
				self.book_title[lang] = title.text
			else:
				self.book_title["_"] = title.text

	def sync_genres(self):
		self.genres: Dict[str, Genre] = {}

		genre_items = self._info.findall(f"{self._ns.ACBFns}genre")
		for genre in genre_items:
			new_genre = Genre(genre.text)

			if "match" in genre.keys():
				new_genre.Match = int(genre.attrib["match"])

			self.genres[new_genre.Genre.name] = new_genre

	def sync_annotations(self):
		self.annotations: Dict[str, str] = {}

		annotation_items = self._info.findall(f"{self._ns.ACBFns}annotation")
		for an in annotation_items:
			p = []
			for i in an.findall(f"{self._ns.ACBFns}p"):
				p.append(i.text)
			p = "\n".join(p)

			if "lang" in an.keys():
				lang = langcodes.standardize_tag(an.attrib["lang"])
				self.annotations[lang] = p
			else:
				self.annotations["_"] = p

	def sync_coverpage(self):
		cpage = self._info.find(f"{self._ns.ACBFns}coverpage")
		self.cover_page: Page = Page(cpage, self.book, True)

	# Optional
	def sync_languages(self):
		self.languages: List[LanguageLayer] = []

		if self._info.find(f"{self._ns.ACBFns}languages") is not None:
			text_layers = self._info.find(f"{self._ns.ACBFns}languages").findall(f"{self._ns.ACBFns}text-layer")
			for layer in text_layers:
				show = bool(distutils.util.strtobool(layer.attrib["show"]))
				new_lang = LanguageLayer(layer.attrib["lang"], show)

				self.languages.append(new_lang)

	def sync_characters(self):
		self.characters: List[str] = []

		character_item = self._info.find(f"{self._ns.ACBFns}characters")
		if character_item is not None:
			for c in character_item.findall(f"{self._ns.ACBFns}name"):
				self.characters.append(c.text)

	def sync_keywords(self):
		self.keywords: Dict[str, List[str]] = {}

		keyword_items = self._info.findall(f"{self._ns.ACBFns}keywords")
		for k in keyword_items:
			if "lang" in k.keys():
				lang = langcodes.standardize_tag(k.attrib["lang"])
				self.keywords[lang] = re.split(", |,", k.text)
			else:
				if k.text is not None:
					self.keywords["_"] = re.split(", |,", k.text)

	def sync_series(self):
		self.series: Dict[str, Series] = {}

		series_items = self._info.findall(f"{self._ns.ACBFns}sequence")
		for se in series_items:
			new_se = Series(se.attrib["title"], se.text)

			if "volume" in se.keys():
				new_se.volume = se.attrib["volume"]

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
			new_db = DBRef(db.attrib["dbname"], db.text)

			if "type" in db.keys():
				new_db.type = db.attrib["type"]

			self.database_ref.append(new_db)
	#endregion

class PublishInfo:
	"""Metadata about the book's publisher.

	See Also
	--------
	`Publish-Info section <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Publish-Info_Section>`_.

	Attributes
	----------
	book : ACBFBook
		Book that the metadata belongs to.

	publisher : str
		Name of the publisher.

	publish_date_string : str
		Date when the book was published as a human readable string.

	publish_date : datetime.date, optional
		Date when the book was published.

	publish_city : str, optional
		City where the book was published.

	isbn : str, optional
		International Standard Book Number.

	license : str, optional
		The license that the book is under.
	"""
	def __init__(self, info, book: ACBFBook):
		self.book = book
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
	"""Metadata about the ACBF file itself.

	See Also
	--------
	`Document-Info section <https://acbf.fandom.com/wiki/Meta-data_Section_Definition#Document-Info_Section>`_.

	Attributes
	----------
	book : ACBFBook
		Book that the metadata belongs to.

	authors : List[Author]
		List of authors of the ACBF file as :class:`Author <libacbf.structs.Author>` objects.

	creation_date_string : str
		Date when the ACBF file was created as a human readable string.

	creation_date : datetime.date, optional
		Date when the ACBF file was created.

	source : str, optional
		A multiline string with information if this book is a derivative of another work. May contain
		URL and other source descriptions.

	document_id : str, optional
		Unique Document ID. Used to distinctly define ACBF files for cataloguing.

	document_version : str, optional
		Version of ACBF file.

	document_history : str, optional
		Change history of the ACBF file with change information in a list of strings.
	"""
	def __init__(self, info, book: ACBFBook):
		self.book = book
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

		self.document_history: Optional[List[str]] = []
		if info.find(f"{ns.ACBFns}history") is not None:
			for item in info.findall(f"{ns.ACBFns}history/{ns.ACBFns}p"):
				self.document_history.append(item.text)

def update_authors(author_items, ns: BookNamespace):
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
