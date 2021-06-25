from __future__ import annotations
import re
import distutils.util
import langcodes
from typing import TYPE_CHECKING, Dict, List, Set, Optional, Union
from datetime import date
import dateutil.parser
from lxml import etree

if TYPE_CHECKING:
	from libacbf import ACBFBook
from libacbf.body import Page
import libacbf.structs as structs
import libacbf.constants as constants
import libacbf.helpers as helpers

def update_authors(author_items, ns) -> List[structs.Author]:
	authors = []

	for au in author_items:
		new_first_name = None
		new_last_name = None
		new_nickname = None
		if au.find(f"{ns}first-name") is not None:
			new_first_name = au.find(f"{ns}first-name").text
		if au.find(f"{ns}last-name") is not None:
			new_last_name = au.find(f"{ns}last-name").text
		if au.find(f"{ns}nickname") is not None:
			new_nickname = au.find(f"{ns}nickname").text

		new_author: structs.Author = structs.Author(new_first_name, new_last_name, new_nickname)
		new_author._element = au

		if "activity" in au.keys():
			new_author.activity = au.attrib["activity"]
		if "lang" in au.keys():
			new_author.lang = au.attrib["lang"]

		# Optional
		if au.find(f"{ns}middle-name") is not None:
			new_author.middle_name = au.find(f"{ns}middle-name").text
		if au.find(f"{ns}home-page") is not None:
			new_author.home_page = au.find(f"{ns}home-page").text
		if au.find(f"{ns}email") is not None:
			new_author.email = au.find(f"{ns}email").text

		authors.append(new_author)

	return authors

def add_author(section: Union[BookInfo, DocumentInfo], author: structs.Author):
	info_section = section._info

	au_element = etree.Element(f"{section._ns}author")
	idx = info_section.index(info_section.findall(f"{section._ns}author")[-1]) + 1
	info_section.insert(idx, au_element)
	author._element = au_element

	attributes = author.__dict__.copy()
	attributes.pop("_element")
	attributes["activity"] = attributes["_activity"]
	attributes.pop("_activity")
	attributes["lang"] = attributes["_lang"]
	attributes.pop("_lang")
	attributes["first_name"] = attributes["_first_name"]
	attributes.pop("_first_name")
	attributes["last_name"] = attributes["_last_name"]
	attributes.pop("_last_name")

	edit_author(section, author, **attributes)

def edit_author(section: Union[BookInfo, DocumentInfo], author: Union[int, structs.Author], **attributes):
	au_list = section._info.findall(f"{section._ns}author")

	if isinstance(author, int):
		au_element = section.authors[author]._element
		author = section.authors[author]
	elif isinstance(author, structs.Author):
		if author._element is None:
			raise ValueError("Author is not part of a book.")
		elif author._element not in au_list:
			raise ValueError("Author is not part of this book.")
		else:
			au_element = author._element

	for i in attributes.keys():
		if not hasattr(author, i):
			raise AttributeError(f"`Author` has no attribute `{i}`.")

	names = {x: attributes[x] for x in ["first_name", "last_name", "nickname"] if x in attributes}

	if len(names) > 0:
		for i in ["first_name", "last_name", "nickname"]:
			if i not in names:
				names[i] = getattr(author, i)
		_ = structs.Author(**names)

	attrs = {x: attributes.pop(x) for x in ["activity", "lang"] if x in attributes}

	for k, v in attrs.items():
		if (k == "activity" and (type(v) is constants.AuthorActivities or v is None)) or (k == "lang" and (isinstance(v, str) or v is None)):
			if v is not None:
				au_element.set(k, v.name if k == "activity" else v)
			else:
				if k in au_element.attrib:
					au_element.attrib.pop(k)
		else:
			raise TypeError(f"`{k}` is not of an accepted type.")

	for k, v in attributes.items():
		if isinstance(v, str) or v is None:
			element = au_element.find(section._ns + re.sub(r'_', '-', k))
			if v is not None and element is None:
				element = etree.Element(section._ns + re.sub(r'_', '-', k))
				au_element.append(element)
				element.text = v
			elif v is not None and element is not None:
				element.text = v
			elif v is None and element is not None:
				element.clear()
				au_element.remove(element)
		else:
			raise TypeError(f"`{k}` is not of an accepted type.")

	section.sync_authors()

def remove_author(section: Union[BookInfo, DocumentInfo], author: Union[int, structs.Author]):
	info_section = section._info

	au_list = section._info.findall(f"{section._ns}author")

	if isinstance(author, int):
		author_element = section.authors[author]._element
	elif isinstance(author, structs.Author):
		if author._element is None:
			raise ValueError("Author is not part of a book.")
		elif author._element not in au_list:
			raise ValueError("Author is not part of this book.")
		author_element = author._element

	author_element.clear()
	info_section.remove(author_element)

	section.sync_authors()

def edit_optional(tag: str, section: Union[BookInfo, PublishInfo, DocumentInfo], attr: str, text: Optional[str]):
	item = section._info.find(section._ns + tag)

	if text is not None:
		if item is None:
			item = etree.Element(section._ns + tag)
			section._info.append(item)
		item.text = text
		setattr(section, attr, item.text)
	elif text is None and item is not None:
		item.clear()
		item.getparent().remove(item)

def edit_date(tag: str, section: Union[BookInfo, PublishInfo, DocumentInfo], attr_s: str, attr_d: str,
			dt: Union[str, date], include_date: bool = True):

	item = section._info.find(section._ns + tag)

	if isinstance(dt, str):
		item.text = dt
	elif isinstance(dt, date):
		item.text = dt.isoformat()

	setattr(section, attr_s, item.text)

	if include_date:
		if isinstance(dt, str):
			item.set("value", dateutil.parser.parse(dt, fuzzy=True).date().isoformat())
		elif isinstance(dt, date):
			item.set("value", dt.isoformat())
		setattr(section, attr_d, date.fromisoformat(item.attrib["value"]))
	else:
		if "value" in item.attrib.keys():
			item.attrib.pop("value")
		setattr(section, attr_d, None)

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
		self._ns: str = book._namespace

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
		self.authors: List[structs.Author] = update_authors(self._info.findall(f"{self._ns}author"), self._ns)

	def sync_book_titles(self):
		self.book_title: Dict[str, str] = {}

		book_items = self._info.findall(f"{self._ns}book-title")
		for title in book_items:
			if "lang" in title.keys():
				lang = langcodes.standardize_tag(title.attrib["lang"])
				self.book_title[lang] = title.text
			else:
				self.book_title['_'] = title.text

	def sync_genres(self):
		self.genres: Dict[str, structs.Genre] = {}

		genre_items = self._info.findall(f"{self._ns}genre")
		for genre in genre_items:
			new_genre = structs.Genre(genre.text)

			if "match" in genre.keys():
				new_genre.Match = int(genre.attrib["match"])

			self.genres[new_genre.Genre.name] = new_genre

	def sync_annotations(self):
		self.annotations: Dict[str, str] = {}

		annotation_items = self._info.findall(f"{self._ns}annotation")
		for an in annotation_items:
			p = []
			for i in an.findall(f"{self._ns}p"):
				p.append(i.text)
			p = "\n".join(p)

			if "lang" in an.keys():
				lang = langcodes.standardize_tag(an.attrib["lang"])
				self.annotations[lang] = p
			else:
				self.annotations['_'] = p

	def sync_coverpage(self):
		cpage = self._info.find(f"{self._ns}coverpage")
		self.cover_page: Page = Page(cpage, self.book, True)

	# --- Optional ---
	def sync_languages(self):
		self.languages: List[structs.LanguageLayer] = []

		if self._info.find(f"{self._ns}languages") is not None:
			text_layers = self._info.find(f"{self._ns}languages").findall(f"{self._ns}text-layer")
			for layer in text_layers:
				show = bool(distutils.util.strtobool(layer.attrib["show"]))
				new_lang = structs.LanguageLayer(langcodes.standardize_tag(layer.attrib["lang"]), show)
				new_lang._element = layer

				self.languages.append(new_lang)

	def sync_characters(self):
		self.characters: List[str] = []

		character_item = self._info.find(f"{self._ns}characters")
		if character_item is not None:
			for c in character_item.findall(f"{self._ns}name"):
				self.characters.append(c.text)

	def sync_keywords(self):
		self.keywords: Dict[str, Set[str]] = {}

		keyword_items = self._info.findall(f"{self._ns}keywords")
		for k in keyword_items:
			if "lang" in k.keys():
				lang = langcodes.standardize_tag(k.attrib["lang"])
			else:
				lang = '_'

			if k.text is not None:
				self.keywords[lang] = {x.lower() for x in re.split(", |,", k.text)}

	def sync_series(self):
		self.series: Dict[str, structs.Series] = {}

		series_items = self._info.findall(f"{self._ns}sequence")
		for se in series_items:
			new_se = structs.Series(se.attrib["title"], se.text)

			if "volume" in se.keys():
				new_se.volume = se.attrib["volume"]

			self.series[se.attrib["title"]] = new_se

	def sync_content_rating(self):
		self.content_rating: Dict[str, str] = {}

		rating_items = self._info.findall(f"{self._ns}content-rating")
		for rt in rating_items:
			if "type" in rt.keys():
				self.content_rating[rt.attrib["type"]] = rt.text
			else:
				self.content_rating['_'] = rt.text

	def sync_database_ref(self):
		self.database_ref: List[structs.DBRef] = []

		db_items = self._info.findall(f"{self._ns}databaseref")
		for db in db_items:
			new_db = structs.DBRef(db.attrib["dbname"], db.text)
			new_db._element = db

			if "type" in db.keys():
				new_db.type = db.attrib["type"]

			self.database_ref.append(new_db)

	#endregion

	#region Editing
	# Author
	@helpers.check_book
	def add_author(self, author: structs.Author):
		add_author(self, author)

	@helpers.check_book
	def edit_author(self, author: Union[structs.Author, int], **attributes):
		edit_author(self, author, **attributes)

	@helpers.check_book
	def remove_author(self, author: Union[int, structs.Author]):
		remove_author(self, author)

	# Titles
	@helpers.check_book
	def edit_title(self, title: str, lang: str = '_'):
		title_elements = self._info.findall(f"{self._ns}book-title")
		idx = self._info.index(title_elements[-1]) + 1

		t_element = None
		if lang == '_':
			for i in title_elements:
				if "lang" not in i.keys():
					t_element = i
					break
		else:
			key = langcodes.standardize_tag(lang)
			for i in title_elements:
				if "lang" in i.keys() and langcodes.standardize_tag(i.attrib["lang"]) == key:
					t_element = i
					break

		if t_element == None:
			t_element = etree.Element(f"{self._ns}book-title")
			self._info.insert(idx, t_element)

		t_element.set("lang", key)
		t_element.text = title

		self.sync_book_titles()

	@helpers.check_book
	def remove_title(self, lang: str = '_'):
		title_elements = self._info.findall(f"{self._ns}book-title")

		if lang == '_':
			for i in title_elements:
				if "lang" not in i.keys():
					i.clear()
					self._info.remove(i)
					self.sync_book_titles()
					break
		else:
			lang = langcodes.standardize_tag(lang)
			for i in title_elements:
				if "lang" in i.keys() and langcodes.standardize_tag(i.attrib["lang"]) == lang:
					i.clear()
					self._info.remove(i)
					self.sync_book_titles()
					break

	# Genres
	@helpers.check_book
	def edit_genre(self, genre: constants.Genres, match: Optional[int] = '_'):
		gn_elements = self._info.findall(f"{self._ns}genre")
		name = genre.name

		gn_element = None
		for i in gn_elements:
			if i.text == name:
				gn_element = i
				break

		if gn_element is None:
			idx = self._info.index(gn_elements[-1]) + 1
			gn_element = etree.Element(f"{self._ns}genre")
			gn_element.text = name
			self._info.insert(idx, gn_element)

		if match is not None and match != '_':
			gn_element.set("match", str(match))
		elif match is None:
			gn_element.attrib.pop("match")

		self.sync_genres()

	@helpers.check_book
	def remove_genre(self, genre: constants.Genres):
		gn_elements = self._info.findall(f"{self}genre")
		name = genre.name

		for i in gn_elements:
			if i.text == name:
				i.clear()
				self._info.remove(i)
				self.sync_genres()
				break

	# Annotations
	@helpers.check_book
	def edit_annotation(self, text: str, lang: str = '_'):
		annotation_elements = self._info.findall(f"{self._ns}annotation")

		an_element = None
		if lang == '_':
			for i in annotation_elements:
				if "lang" not in i.keys():
					an_element = i
					break
		else:
			lang = langcodes.standardize_tag(lang)
			for i in annotation_elements:
				if "lang" in i.keys() and langcodes.standardize_tag(i.attrib["lang"]) == lang:
					an_element = i
					break

		if an_element is None:
			idx = self._info.index(annotation_elements[-1]) + 1
			an_element = etree.Element(f"{self._ns}annotation")
			self._info.insert(idx, an_element)

		an_element.clear()
		an_element.set("lang", lang)

		for pt in text.split(r'\n'):
			p = etree.Element(f"{self._ns}p")
			p.text = pt
			an_element.append(p)

		self.sync_annotations()

	@helpers.check_book
	def remove_annotation(self, lang: str = '_'):
		annotation_elements = self._info.findall(f"{self._ns}annotation")

		an_element = None
		if lang == '_':
			for i in annotation_elements:
				if "lang" not in i.keys():
					an_element = i
					break
		else:
			lang = langcodes.standardize_tag(lang)
			for i in annotation_elements:
				if "lang" in i.keys() and langcodes.standardize_tag(i.attrib["lang"]) == lang:
					an_element = i
					break

		if an_element is not None:
			an_element.clear()
			self._info.remove(an_element)
			self.sync_annotations()

	# --- Optional ---
	# Languages
	@helpers.check_book
	def add_language(self, lang: str, show: bool):
		ln_section = self._info.find(f"{self._ns}languages")
		if ln_section is None:
			ln_section = etree.Element(f"{self._ns}languages")
			self._info.append(ln_section)

		lang = langcodes.standardize_tag(lang)

		ln_item = etree.Element(f"{self._ns}text-layer")
		ln_item.set("lang", lang)
		ln_item.set("show", str(show).lower())
		ln_section.append(ln_item)

		self.sync_languages()

	@helpers.check_book
	def edit_language(self, layer: Union[int, structs.LanguageLayer], lang: Optional[str] = None, show: Optional[bool] = None):
		if lang is None and show is None:
			return

		if isinstance(layer, int):
			layer = self.languages[layer]

		if layer not in self.languages:
			raise ValueError("`layer` is not a part of the book.")

		if lang is not None:
			layer._element.set("lang", lang)
		if show is not None:
			layer._element.set("show", str(show).lower())
		self.sync_languages()

	@helpers.check_book
	def remove_language(self, layer: Union[int, structs.LanguageLayer]):
		ln_section = self._info.find(f"{self._ns}languages")

		if isinstance(layer, int):
			layer = self.languages[layer]

		layer._element.clear()
		ln_section.remove(layer._element)

		if len(ln_section.findall(f"{self._ns}text-layer")) == 0:
			ln_section.clear()
			ln_section.getparent().remove(ln_section)

		self.sync_languages()

	# Characters
	@helpers.check_book
	def add_character(self, name: str):
		char_section = self._info.find(f"{self._ns}characters")

		if char_section is None:
			char_section = etree.Element(f"{self._ns}characters")

		char = etree.Element(f"{self._ns}name")
		char.text = name
		char_section.append(char)
		self.sync_characters()

	@helpers.check_book
	def remove_character(self, item: Union[str, int]):
		char_section = self._info.find(f"{self._ns}characters")

		if char_section is not None:
			char_elements = char_section.findall(f"{self._ns}name")

			if isinstance(item, int):
				char_elements[item].clear()
				char_section.remove(char_elements[item])
			elif isinstance(item, str):
				for i in char_elements:
					if i.text == item:
						i.clear()
						char_section.remove(i)
						break

			if len(char_section.findall(f"{self._ns}name")) == 0:
				char_section.clear()
				char_section.getparent().remove(char_section)

			self.sync_characters()

	# Keywords
	@helpers.check_book
	def add_keyword(self, *kwords: str, lang: str = '_'):
		key_elements = self._info.findall(f"{self._ns}keywords")
		idx = None

		if len(key_elements) > 0:
			idx = self._info.index(key_elements[-1]) + 1

		key_element = None
		if lang == '_':
			for i in key_elements:
				if "lang" not in i.keys():
					key_element = i
					break
		else:
			lang = langcodes.standardize_tag(lang)
			for i in key_elements:
				if "lang" in i.keys() and langcodes.standardize_tag(i.attrib["lang"]) == lang:
					key_element = i
					break

		if key_element is None:
			key_element = etree.Element(f"{self._ns}keywords")
			if idx is not None:
				self._info.insert(idx, key_element)
			else:
				self._info.append(key_element)

		if lang != '_':
			key_element.set("lang", lang)

		kwords = {x.lower() for x in kwords}
		keywords = set([])
		if lang in self.keywords:
			keywords = self.keywords[lang].copy()
		keywords.update(kwords)
		key_element.text = ", ".join(keywords)

		self.sync_keywords()

	@helpers.check_book
	def remove_keyword(self, *kwords: str, lang: str = '_'):
		key_elements = self._info.findall(f"{self._ns}keywords")

		key_element = None
		if lang == '_':
			for i in key_elements:
				if "lang" not in i.keys():
					key_element = i
					break
		else:
			lang = langcodes.standardize_tag(lang)
			for i in key_elements:
				if "lang" in i.keys() and langcodes.standardize_tag(i.attrib["lang"]) == lang:
					key_element = i
					break

		kwords = {x.lower() for x in kwords}
		keywords = set([])
		if lang in self.keywords:
			keywords = self.keywords[lang].copy()
		keywords.difference_update(kwords)
		key_element.text = ", ".join(keywords)

		self.sync_keywords()

	@helpers.check_book
	def clear_keywords(self, lang: str = '_'):
		key_elements = self._info.findall(f"{self._ns}keywords")
		key_element = None
		if lang == '_':
			for i in key_elements:
				if "lang" not in i.keys():
					key_element = i
					break
		else:
			lang = langcodes.standardize_tag(lang)
			for i in key_elements:
				if "lang" in i.keys() and langcodes.standardize_tag(i.attrib["lang"]) == lang:
					key_element = i
					break
		if key_element is not None:
			key_element.clear()
			key_element.getparent().remove(key_element)
			self.sync_keywords()

	# Series
	@helpers.check_book
	def edit_series(self, title: str, sequence: Optional[str] = None, volume: Optional[str] = '_'):
		ser_items = self._info.findall(f"{self._ns}sequence")
		idx = None

		if sequence is not None:
			sequence = str(sequence)
		if volume is not None:
			volume = str(volume)

		if len(ser_items) > 0:
			idx = self._info.index(ser_items[-1]) + 1

		ser_element = None
		for i in ser_items:
			if i.attrib["title"] == title:
				ser_element = i
				break
		if ser_element is None:
			if sequence is None:
				raise AttributeError(f"`sequence` cannot be blank for new series entry `{title}`.")
			ser_element = etree.Element(f"{self._ns}sequence")
			ser_element.set("title", title)
			if idx is not None:
				self._info.insert(idx, ser_element)
			else:
				self._info.append(ser_element)

		if sequence is not None:
			ser_element.text = sequence

		if volume != '_':
			if volume is not None:
				ser_element.set("volume", volume)
			else:
				if "volume" in ser_element.keys():
					ser_element.attrib.pop("volume")

		self.sync_series()

	@helpers.check_book
	def remove_series(self, title: str):
		seq_items = self._info.findall(f"{self._ns}sequence")

		for i in seq_items:
			if i.attrib["title"] == title:
				i.clear()
				i.getparent().remove(i)
				self.sync_series()
				break

	# Content Rating
	@helpers.check_book
	def edit_content_rating(self, rating: str, type: str = '_'):
		rt_items = self._info.findall(f"{self._ns}content-rating")
		idx = None

		if len(rt_items) > 0:
			idx = self._info.index(rt_items[-1]) + 1

		rt_element = None
		if type != '_':
			for i in rt_items:
				if "type" in i.keys() and i.attrib["type"] == type:
					rt_element = i
					break
		else:
			for i in rt_items:
				if "type" not in i.keys():
					rt_element = i
					break

		if rt_element is None:
			rt_element = etree.Element(f"{self._ns}content-rating")
			if idx is not None:
				self._info.insert(idx, rt_element)
			else:
				self._info.append(rt_element)
			if type != '_':
				rt_element.set("type", type)

		rt_element.text = rating
		self.sync_content_rating()

	@helpers.check_book
	def remove_content_rating(self, type: str = '_'):
		rt_items = self._info.findall(f"{self._ns}content-rating")

		rt_element = None
		for i in rt_items:
			if (type == '_' and "type" not in i.keys()) or (type != '_' and "type" in i.keys() and i.attrib["type"] == type):
				rt_element = i
				break

		if rt_element is not None:
			rt_element.clear()
			rt_element.getparent().remove(rt_element)
			self.sync_content_rating()

	# Database Ref
	@helpers.check_book
	def add_database_ref(self, dbname: str, ref: str, type: Optional[str] = None):
		db_items = self._info.findall(f"{self._ns}databaseref")
		idx = None

		if len(db_items) > 0:
			idx = self._info.index(db_items[-1]) + 1

		db_element = etree.Element(f"{self._ns}databaseref")
		db_element.set("dbname", dbname)
		db_element.text = ref
		if type is not None:
			db_element.set("type", type)

		if idx is not None:
			self._info.insert(idx, db_element)
		else:
			self._info.append(db_element)

		self.sync_database_ref()

	@helpers.check_book
	def edit_database_ref(self, dbref: Union[int, structs.DBRef], dbname: Optional[str] = None, ref: Optional[str] = None, type: Optional[str] = '_'):
		if isinstance(dbref, int):
			dbref = self.database_ref[dbref]

		if dbname is not None:
			dbref._element.set("dbname", dbname)
		if ref is not None:
			dbref._element.text = ref

		if type != '_':
			if type is not None:
				dbref._element.set("type", type)
			else:
				if "type" in dbref._element.keys():
					dbref._element.attrib.pop("type")

		if dbname is not None or ref is not None or type != '_':
			self.sync_database_ref()

	@helpers.check_book
	def remove_database_ref(self, dbref: Union[int, structs.DBRef]):
		if isinstance(dbref, int):
			dbref = self.database_ref[dbref]

		dbref._element.clear()
		dbref._element.getparent().remove(dbref._element)
		self.sync_database_ref()

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
		self._ns = book._namespace
		self._info = info

		self.book = book

		self.publisher: str = info.find(f"{self._ns}publisher").text

		self.publish_date_string: str = info.find(f"{self._ns}publish-date").text

		# --- Optional ---
		self.publish_date: Optional[date] = None
		if "value" in info.find(f"{self._ns}publish-date").keys():
			self.publish_date = date.fromisoformat(info.find(f"{self._ns}publish-date").attrib["value"])

		self.publish_city: Optional[str] = None
		if info.find(f"{self._ns}city") is not None:
			self.publish_city = info.find(f"{self._ns}city").text

		self.isbn: Optional[str] = None
		if info.find(f"{self._ns}isbn") is not None:
			self.isbn = info.find(f"{self._ns}isbn").text

		self.license: Optional[str] = None
		if info.find(f"{self._ns}license") is not None:
			self.license = info.find(f"{self._ns}license").text

	@helpers.check_book
	def set_publisher(self, name: str):
		pub_item = self._info.find(f"{self._ns}publisher")
		pub_item.text = name
		self._publisher = pub_item.text

	@helpers.check_book
	def set_publish_date(self, dt: Union[str, date], include_date: bool = True):
		edit_date("publish-date",
						self,
						"publish_date_string",
						"publish_date",
						dt,
						include_date
		)

	# --- Optional ---
	@helpers.check_book
	def set_publish_city(self, city: Optional[str]):
		edit_optional("city", self, "publish_city", city)

	@helpers.check_book
	def set_isbn(self, isbn: Optional[str]):
		edit_optional("isbn", self, "isbn", isbn)

	@helpers.check_book
	def set_license(self, license: Optional[str]):
		edit_optional("license", self, "license", license)

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
		self._info = info
		self._ns = book._namespace

		self.sync_authors()

		self.creation_date_string: str = info.find(f"{self._ns}creation-date").text

		# --- Optional ---
		self.creation_date: Optional[date] = None
		if "value" in info.find(f"{self._ns}creation-date").keys():
			self.creation_date = date.fromisoformat(info.find(f"{self._ns}creation-date").attrib["value"])

		self.source: Optional[str] = None
		if info.find(f"{self._ns}source") is not None:
			p = []
			for line in info.findall(f"{self._ns}source/{self._ns}p"):
				p.append(line.text)
			self.source = "\n".join(p)

		self.document_id: Optional[str] = None
		if info.find(f"{self._ns}id") is not None:
			self.document_id = info.find(f"{self._ns}id").text

		self.document_version: Optional[str] = None
		if info.find(f"{self._ns}version") is not None:
			self.document_version = info.find(f"{self._ns}version").text

		self.sync_history()

	@helpers.check_book
	def sync_authors(self):
		self.authors: List[structs.Author] = update_authors(self._info.findall(f"{self._ns}author"), self._ns)

	@helpers.check_book
	def sync_history(self):
		self.document_history: Optional[List[str]] = []
		for item in self._info.findall(f"{self._ns}history/{self._ns}p"):
			self.document_history.append(item.text)

	# Author
	@helpers.check_book
	def add_author(self, author: structs.Author):
		add_author(self, author)

	@helpers.check_book
	def edit_author(self, author: Union[structs.Author, int], **attributes):
		edit_author(self, author, **attributes)

	@helpers.check_book
	def remove_author(self, author: Union[int, structs.Author]):
		remove_author(self, author)
	# Author

	@helpers.check_book
	def set_creation_date(self, dt: Union[str, date], include_date: bool = True):
		edit_date("creation-date",
						self,
						"creation_date_string",
						"creation_date",
						dt,
						include_date
		)

	# --- Optional ---
	@helpers.check_book
	def set_source(self, source: Optional[str]):
		src_section = self._info.find(f"{self._ns}source")

		if source is not None:
			if src_section is None:
				src_section = etree.Element(f"{self._ns}source")
				self._info.append(src_section)
			src_section.clear()
			for i in re.split('\n', source):
				p = etree.Element(f"{self._ns}p")
				src_section.append(p)
				p.text = i
		else:
			if src_section is not None:
				src_section.clear()
				src_section.getparent().remove(src_section)

	@helpers.check_book
	def set_document_id(self, id: Optional[str]):
		edit_optional("id", self, "document_id", id)

	@helpers.check_book
	def set_document_version(self, version: Optional[str] = None):
		edit_optional("version", self, "document_version", version)

	# History
	@helpers.check_book
	def insert_history(self, index: int, entry: str):
		history_section = self._info.find(f"{self._ns}history")
		if history_section is None:
			history_section = etree.SubElement(self._info, f"{self._ns}history")

		p = etree.Element(f"{self._ns}p")
		history_section.insert(index, p)
		p.text = entry
		self.sync_history()

	@helpers.check_book
	def append_history(self, entry: str):
		idx = len(self._info.findall(f"{self._ns}history/{self._ns}p"))
		self.insert_history(idx, entry)

	@helpers.check_book
	def edit_history(self, index: int, text: str):
		item = self._info.findall(f"{self._ns}history/{self._ns}p")[index]
		item.text = text
		self.sync_history()

	@helpers.check_book
	def remove_history(self, index: int):
		item = self._info.findall(f"{self._ns}history/{self._ns}p")[index]
		item.clear()
		item.getparent().remove(item)

		history_section = self._info.find(f"{self._ns}history")
		if len(history_section.findall(f"{self._ns}p")) == 0:
			history_section.clear()
			self._info.remove(history_section)
		self.sync_history()
