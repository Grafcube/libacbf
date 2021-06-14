import re
import langcodes
import magic
import dateutil.parser
from typing import Optional, Union
from datetime import date
from functools import wraps
from pathlib import Path
from base64 import b64encode
from lxml import etree

from libacbf import ACBFBook
from libacbf.structs import Author, DBRef, LanguageLayer
from libacbf.constants import ArchiveTypes, AuthorActivities, Genres
from libacbf.metadata import BookInfo, DocumentInfo, PublishInfo

def check_book(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		book: ACBFBook = kwargs["book"] if "book" in kwargs.keys() else args[0]
		if book.archive is not None and book.archive.type == ArchiveTypes.Rar:
			raise ValueError("Editing RAR Archives is not supported by this module.")
		if not book.is_open:
			raise ValueError("I/O operation on closed file.")
		func(*args, **kwargs)
	return wrapper

def add_author(book: ACBFBook, section: Union[BookInfo, PublishInfo, DocumentInfo], author: Author):
	info_section = section._info

	if section not in [book.Metadata.book_info, book.Metadata.publisher_info, book.Metadata.document_info]:
		raise ValueError("Section is not from this book.")

	au_element = etree.Element(f"{book.namespace}author")
	idx = info_section.index(info_section.findall(f"{book.namespace}author")[-1]) + 1
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

	edit_author(book, section, author, **attributes)

def edit_author(book: ACBFBook, section: Union[BookInfo, PublishInfo, DocumentInfo], author: Union[int, Author], **attributes):
	au_list = section._info.findall(f"{book.namespace}author")

	if section not in [book.Metadata.book_info, book.Metadata.publisher_info, book.Metadata.document_info]:
		raise ValueError("Section is not from this book.")

	if isinstance(author, int):
		au_element = section.authors[author]._element
		author = section.authors[author]
	elif isinstance(author, Author):
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
		_ = Author(**names)

	attrs = {x: attributes.pop(x) for x in ["activity", "lang"] if x in attributes}

	for k, v in attrs.items():
		if (k == "activity" and (type(v) is AuthorActivities or v is None)) or (k == "lang" and (isinstance(v, str) or v is None)):
			if v is not None:
				au_element.set(k, v.name if k == "activity" else v)
			else:
				if k in au_element.attrib:
					au_element.attrib.pop(k)
		else:
			raise TypeError(f"`{k}` is not of an accepted type.")

	for k, v in attributes.items():
		if isinstance(v, str) or v is None:
			element = au_element.find(book.namespace + re.sub(r'_', '-', k))
			if v is not None and element is None:
				element = etree.Element(book.namespace + re.sub(r'_', '-', k))
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

def remove_author(book: ACBFBook, section: Union[BookInfo, PublishInfo, DocumentInfo], author: Union[int, Author]):
	info_section = section._info

	if section not in [book.Metadata.book_info, book.Metadata.publisher_info, book.Metadata.document_info]:
		raise ValueError("Section is not from this book.")

	au_list = section._info.findall(f"{book.namespace}author")

	if isinstance(author, int):
		author_element = section.authors[author]._element
	elif isinstance(author, Author):
		if author._element is None:
			raise ValueError("Author is not part of a book.")
		elif author._element not in au_list:
			raise ValueError("Author is not part of this book.")
		author_element = author._element

	author_element.clear()
	info_section.remove(author_element)

	section.sync_authors()

def edit_optional(book: ACBFBook, tag: str, section: Union[BookInfo, PublishInfo, DocumentInfo], attr: str, text: Optional[str] = None):
	item = section._info.find(book.namespace + tag)

	if text is not None:
		if item is None:
			item = etree.Element(book.namespace + tag)
			section._info.append(item)
		item.text = text
		setattr(section, attr, item.text)
	elif text is None and item is not None:
		item.clear()
		item.getparent().remove(item)

def edit_date(book: ACBFBook, tag: str, section: Union[BookInfo, PublishInfo, DocumentInfo], attr_s: str, attr_d: str, dt: Union[str, date], include_date: bool = True):
	item = section._info.find(book.namespace + tag)

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

class book:
	class data: # Incomplete (Archive writing)
		@staticmethod
		@check_book
		def add(book: ACBFBook, file_path: Union[str, Path], embed: bool = False):
			# TODO: Option to choose whether to embed in xml or add to archive
			file_path = Path(file_path) if isinstance(file_path, str) else file_path

			dat_section = book._root.find(f"{book.namespace}data")
			if dat_section is None:
				dat_section = etree.Element(f"{book.namespace}data")
				book._root.append(dat_section)

			id = file_path.name
			with open(file_path, 'rb') as file:
				contents = file.read()
				content_type = magic.from_buffer(contents, True)
				data64 = str(b64encode(contents), encoding="utf-8")

			bin_element = etree.Element(f"{book.namespace}binary")
			bin_element.set("id", id)
			bin_element.set("content-type", content_type)
			bin_element.text = data64

			dat_section.append(bin_element)
			book.Data.sync_data()

		@staticmethod
		@check_book
		def remove(book: ACBFBook, id: str):
			dat_section = book._root.find(f"{book.namespace}data")

			if dat_section is not None:
				for i in dat_section.findall(f"{book.namespace}binary"):
					if i.attrib["id"] == id:
						i.clear()
						dat_section.remove(i)
						break

				if len(dat_section.findall(f"{book.namespace}binary")) == 0:
					dat_section.clear()
					dat_section.getparent().remove(dat_section)

				book.Data.sync_data()

	class references:
		@staticmethod
		@check_book
		def edit(book: ACBFBook, id: str, paragraph: str):
			ref_section = book._root.find(f"{book.namespace}references")
			if ref_section is None:
				ref_section = etree.Element(f"{book.namespace}references")
				book._root.append(ref_section)

			ref_items = ref_section.findall(f"{book.namespace}reference")

			ref_element = None
			for i in ref_items:
				if i.attrib["id"] == id:
					ref_element = i
					break

			if ref_element == None:
				ref_element = etree.Element(f"{book.namespace}reference")
				ref_section.append(ref_element)

			ref_element.clear()
			ref_element.set("id", id)

			p_list = re.split(r"\n", paragraph)
			for ref in p_list:
				p = f"<p>{ref}</p>"
				p_element = etree.fromstring(bytes(p, encoding="utf-8"))
				for i in list(p_element.iter()):
					i.tag = book.namespace + i.tag
				ref_element.append(p_element)

			book.sync_references()

		@staticmethod
		@check_book
		def remove(book: ACBFBook, id: str):
			ref_section = book._root.find(f"{book.namespace}references")

			if ref_section is not None:
				for i in ref_section.findall(f"{book.namespace}reference"):
					if i.attrib["id"] == id:
						i.clear()
						ref_section.remove(i)
						break

				if len(ref_section.findall(f"{book.namespace}reference")) == 0:
					ref_section.getparent().remove(ref_section)

				book.sync_references()

	class styles: # Incomplete
		@staticmethod
		@check_book
		def edit(book: ACBFBook, stylesheet: str, style_name: str = "_"):

			book.Styles.sync_styles()

		@staticmethod
		@check_book
		def remove(book: ACBFBook, style_name: str = "_"):

			book.Styles.sync_styles()

class metadata:
	class bookinfo:
		class authors:
			@staticmethod
			@check_book
			def add(book: ACBFBook, author: Author):
				add_author(book, book.Metadata.book_info, author)

			@staticmethod
			@check_book
			def edit(book: ACBFBook, author: Union[Author, int], **attributes):
				edit_author(book, book.Metadata.book_info, author, **attributes)

			@staticmethod
			@check_book
			def remove(book: ACBFBook, author: Union[int, Author]):
				remove_author(book, book.Metadata.book_info, author)

		class title:
			@staticmethod
			@check_book
			def edit(book: ACBFBook, title: str, lang: str = "_"):
				info_section = book.Metadata.book_info._info
				title_elements = info_section.findall(f"{book.namespace}book-title")
				idx = info_section.index(title_elements[-1]) + 1

				t_element = None
				if lang == "_":
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
					t_element = etree.Element(f"{book.namespace}book-title")
					info_section.insert(idx, t_element)

				t_element.set("lang", key)
				t_element.text = title

				book.Metadata.book_info.sync_book_titles()

			@staticmethod
			@check_book
			def remove(book: ACBFBook, lang: str = "_"):
				info_section = book.Metadata.book_info._info
				title_elements = info_section.findall(f"{book.namespace}book-title")

				if lang == "_":
					for i in title_elements:
						if "lang" not in i.keys():
							i.clear()
							info_section.remove(i)
							book.Metadata.book_info.sync_book_titles()
							break
				else:
					lang = langcodes.standardize_tag(lang)
					for i in title_elements:
						if "lang" in i.keys() and langcodes.standardize_tag(i.attrib["lang"]) == lang:
							i.clear()
							info_section.remove(i)
							book.Metadata.book_info.sync_book_titles()
							break

		class genres:
			@staticmethod
			@check_book
			def edit(book: ACBFBook, genre: Genres, match: Optional[int] = "_"):
				info_section = book.Metadata.book_info._info
				gn_elements = info_section.findall(f"{book.namespace}genre")
				name = genre.name

				gn_element = None
				for i in gn_elements:
					if i.text == name:
						gn_element = i
						break

				if gn_element is None:
					idx = info_section.index(gn_elements[-1]) + 1
					gn_element = etree.Element(f"{book.namespace}genre")
					gn_element.text = name
					info_section.insert(idx, gn_element)

				if match is not None and match != "_":
					gn_element.set("match", str(match))
				elif match is None:
					gn_element.attrib.pop("match")

				book.Metadata.book_info.sync_genres()

			@staticmethod
			@check_book
			def remove(book: ACBFBook, genre: Genres):
				info_section = book.Metadata.book_info._info
				gn_elements = info_section.findall(f"{book.namespace}genre")
				name = genre.name

				for i in gn_elements:
					if i.text == name:
						i.clear()
						info_section.remove(i)
						book.Metadata.book_info.sync_genres()
						break

		class annotation:
			@staticmethod
			@check_book
			def edit(book: ACBFBook, text: str, lang: str = "_"):
				info_section = book.Metadata.book_info._info
				annotation_elements = info_section.findall(f"{book.namespace}annotation")

				an_element = None
				if lang == "_":
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
					idx = info_section.index(annotation_elements[-1]) + 1
					an_element = etree.Element(f"{book.namespace}annotation")
					info_section.insert(idx, an_element)

				an_element.clear()
				an_element.set("lang", lang)

				for pt in text.split(r'\n'):
					p = etree.Element(f"{book.namespace}p")
					p.text = pt
					an_element.append(p)

				book.Metadata.book_info.sync_annotations()

			@staticmethod
			@check_book
			def remove(book: ACBFBook, lang: str = "_"):
				info_section = book.Metadata.book_info._info
				annotation_elements = info_section.findall(f"{book.namespace}annotation")

				an_element = None
				if lang == "_":
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
					info_section.remove(an_element)
					book.Metadata.book_info.sync_annotations()

		class coverpage: # Incomplete (With Page editing)
			@staticmethod
			@check_book
			def edit(book: ACBFBook):
				raise NotImplementedError("TODO when making Page editor")

		# Optional
		class languagelayers:
			@staticmethod
			@check_book
			def add(book: ACBFBook, lang: str, show: bool):
				ln_section = book.Metadata.book_info._info.find(f"{book.namespace}languages")
				if ln_section is None:
					ln_section = etree.Element(f"{book.namespace}languages")
					book.Metadata.book_info._info.append(ln_section)

				lang = langcodes.standardize_tag(lang)

				ln_item = etree.Element(f"{book.namespace}text-layer")
				ln_item.set("lang", lang)
				ln_item.set("show", str(show))
				ln_section.append(ln_item)

				book.Metadata.book_info.sync_languages()

			@staticmethod
			@check_book
			def edit(book: ACBFBook, layer: Union[int, LanguageLayer], lang: Optional[str] = None, show: Optional[bool] = None):
				if lang is None and show is None:
					return

				if isinstance(layer, int):
					layer = book.Metadata.book_info.languages[layer]

				if lang is not None:
					layer._element.set("lang", lang)
				if show is not None:
					layer._element.set("show", str(show))
				book.Metadata.book_info.sync_languages()

			@staticmethod
			@check_book
			def remove(book: ACBFBook, layer: Union[int, LanguageLayer]):
				ln_section = book.Metadata.book_info._info.find(f"{book.namespace}languages")

				if isinstance(layer, int):
					layer = book.Metadata.book_info.languages[layer]

				layer._element.clear()
				ln_section.remove(layer._element)

				if len(ln_section.findall(f"{book.namespace}text-layer")) == 0:
					ln_section.clear()
					ln_section.getparent().remove(ln_section)

				book.Metadata.book_info.sync_languages()

		class characters:
			@staticmethod
			@check_book
			def add(book: ACBFBook, name: str):
				char_section = book.Metadata.book_info._info.find(f"{book.namespace}characters")

				if char_section is None:
					char_section = etree.Element(f"{book.namespace}characters")

				char = etree.Element(f"{book.namespace}name")
				char.text = name
				char_section.append(char)
				book.Metadata.book_info.sync_characters()

			@staticmethod
			@check_book
			def remove(book: ACBFBook, item: Union[str, int]):
				char_section = book.Metadata.book_info._info.find(f"{book.namespace}characters")

				if char_section is not None:
					char_elements = char_section.findall(f"{book.namespace}name")

					if isinstance(item, int):
						char_elements[item].clear()
						char_section.remove(char_elements[item])
					elif isinstance(item, str):
						for i in char_elements:
							if i.text == item:
								i.clear()
								char_section.remove(i)
								break

					if len(char_section.findall(f"{book.namespace}name")) == 0:
						char_section.clear()
						char_section.getparent().remove(char_section)

					book.Metadata.book_info.sync_characters()

		class keywords:
			@staticmethod
			@check_book
			def add(book: ACBFBook, *kwords: str, lang: str = "_"):
				info_section = book.Metadata.book_info._info
				key_elements = info_section.findall(f"{book.namespace}keywords")
				idx = None

				if len(key_elements) > 0:
					idx = info_section.index(key_elements[-1]) + 1

				key_element = None
				if lang == "_":
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
					key_element = etree.Element(f"{book.namespace}keywords")
					if idx is not None:
						info_section.insert(idx, key_element)
					else:
						info_section.append(key_element)

				if lang != "_":
					key_element.set("lang", lang)

				kwords = {x.lower() for x in kwords}
				keywords = set([])
				if lang in book.Metadata.book_info.keywords:
					keywords = book.Metadata.book_info.keywords[lang].copy()
				keywords.update(kwords)
				key_element.text = ", ".join(keywords)

				book.Metadata.book_info.sync_keywords()

			@staticmethod
			@check_book
			def remove(book: ACBFBook, *kwords: str, lang: str = "_"):
				info_section = book.Metadata.book_info._info
				key_elements = info_section.findall(f"{book.namespace}keywords")

				key_element = None
				if lang == "_":
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
				if lang in book.Metadata.book_info.keywords:
					keywords = book.Metadata.book_info.keywords[lang].copy()
				keywords.difference_update(kwords)
				key_element.text = ", ".join(keywords)

				book.Metadata.book_info.sync_keywords()

			@staticmethod
			@check_book
			def clear(book: ACBFBook, lang: str = "_"):
				key_elements = book.Metadata.book_info._info.findall(f"{book.namespace}keywords")
				key_element = None
				if lang == "_":
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
					book.Metadata.book_info.sync_keywords()

		class series:
			@staticmethod
			@check_book
			def edit(book: ACBFBook, title: str, sequence: Optional[str] = None, volume: Optional[str] = "_"):
				info_section = book.Metadata.book_info._info
				ser_items = info_section.findall(f"{book.namespace}sequence")
				idx = None

				if sequence is not None:
					sequence = str(sequence)
				if volume is not None:
					volume = str(volume)

				if len(ser_items) > 0:
					idx = info_section.index(ser_items[-1]) + 1

				ser_element = None
				for i in ser_items:
					if i.attrib["title"] == title:
						ser_element = i
						break
				if ser_element is None:
					if sequence is None:
						raise AttributeError(f"`sequence` cannot be blank for new series entry `{title}`.")
					ser_element = etree.Element(f"{book.namespace}sequence")
					ser_element.set("title", title)
					if idx is not None:
						info_section.insert(idx, ser_element)
					else:
						info_section.append(ser_element)

				if sequence is not None:
					ser_element.text = sequence

				if volume != "_":
					if volume is not None:
						ser_element.set("volume", volume)
					else:
						if "volume" in ser_element.keys():
							ser_element.attrib.pop("volume")

				book.Metadata.book_info.sync_series()

			def remove(book: ACBFBook, title: str):
				seq_items = book.Metadata.book_info._info.findall(f"{book.namespace}sequence")

				for i in seq_items:
					if i.attrib["title"] == title:
						i.clear()
						i.getparent().remove(i)
						book.Metadata.book_info.sync_series()
						break

		class rating:
			@staticmethod
			@check_book
			def edit(book: ACBFBook, rating: str, type: str = "_"):
				info_section = book.Metadata.book_info._info
				rt_items = info_section.findall(f"{book.namespace}content-rating")
				idx = None

				if len(rt_items) > 0:
					idx = info_section.index(rt_items[-1]) + 1

				rt_element = None
				if type != "_":
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
					rt_element = etree.Element(f"{book.namespace}content-rating")
					if idx is not None:
						info_section.insert(idx, rt_element)
					else:
						info_section.append(rt_element)
					if type != "_":
						rt_element.set("type", type)

				rt_element.text = rating
				book.Metadata.book_info.sync_content_rating()

			@staticmethod
			@check_book
			def remove(book: ACBFBook, type: str = "_"):
				rt_items = book.Metadata.book_info._info.findall(f"{book.namespace}content-rating")

				rt_element = None
				for i in rt_items:
					if (type == "_" and "type" not in i.keys()) or (type != "_" and "type" in i.keys() and i.attrib["type"] == type):
						rt_element = i
						break

				if rt_element is not None:
					rt_element.clear()
					rt_element.getparent().remove(rt_element)
					book.Metadata.book_info.sync_content_rating()

		class databaseref:
			@staticmethod
			@check_book
			def add(book: ACBFBook, dbname: str, ref: str, type: Optional[str] = None):
				info_section = book.Metadata.book_info._info
				db_items = info_section.findall(f"{book.namespace}databaseref")
				idx = None

				if len(db_items) > 0:
					idx = info_section.index(db_items[-1]) + 1

				db_element = etree.Element(f"{book.namespace}databaseref")
				db_element.set("dbname", dbname)
				db_element.text = ref
				if type is not None:
					db_element.set("type", type)

				if idx is not None:
					info_section.insert(idx, db_element)
				else:
					info_section.append(db_element)

				book.Metadata.book_info.sync_database_ref()

			@staticmethod
			@check_book
			def edit(book: ACBFBook, dbref: Union[int, DBRef], dbname: Optional[str] = None, ref: Optional[str] = None, type: Optional[str] = None):
				if isinstance(dbref, int):
					dbref = book.Metadata.book_info.database_ref[dbref]

				if dbname is not None:
					dbref._element.set("dbname", dbname)
				if ref is not None:
					dbref._element.text = ref
				if type is not None:
					dbref._element.set("type", type)

				if dbname is not None or ref is not None or type is not None:
					book.Metadata.book_info.sync_database_ref()

			@staticmethod
			@check_book
			def remove(book: ACBFBook, dbref: DBRef):
				dbref._element.clear()
				dbref._element.getparent().remove(dbref._element)
				book.Metadata.book_info.sync_database_ref()

	class publishinfo:
		@staticmethod
		@check_book
		def publisher(book: ACBFBook, name: str):
			pub_item = book.Metadata.publisher_info._info.find(f"{book.namespace}publisher")
			pub_item.text = name
			book.Metadata.publisher_info.publisher = pub_item.text

		@staticmethod
		@check_book
		def publish_date(book: ACBFBook, dt: Union[str, date], include_date: bool = True):
			edit_date(book,
					"publish-date",
					book.Metadata.publisher_info,
					"publish_date_string",
					"publish_date",
					dt,
					include_date
				)

		# Optional
		@staticmethod
		@check_book
		def publish_city(book: ACBFBook, city: Optional[str] = None):
			edit_optional(book, "city", book.Metadata.publisher_info, "publish_city", city)

		@staticmethod
		@check_book
		def isbn(book: ACBFBook, isbn: Optional[str] = None):
			"""[summary]

			Parameters
			----------
			book : ACBFBook
				[description]
			isbn : Optional[str], optional
				[description], by default None
			"""
			edit_optional(book, "isbn", book.Metadata.publisher_info, "isbn", isbn)

		@staticmethod
		@check_book
		def license(book: ACBFBook, license: Optional[str]):
			"""[summary]

			Parameters
			----------
			book : ACBFBook
				[description]
			license : Optional[str]
				[description]
			"""
			edit_optional(book, "license", book.Metadata.publisher_info, "license", license)

	class documentinfo:
		class authors:
			@staticmethod
			@check_book
			def add(book: ACBFBook, author: Author):
				add_author(book, book.Metadata.document_info, author)

			@staticmethod
			@check_book
			def edit(book: ACBFBook, author: Union[Author, int], **attributes):
				edit_author(book, book.Metadata.document_info, author, **attributes)

			@staticmethod
			@check_book
			def remove(book: ACBFBook, author: Union[int, Author]):
				remove_author(book, book.Metadata.document_info, author)

		@staticmethod
		@check_book
		def creation_date(book: ACBFBook, dt: Union[str, date], include_date: bool = True):
			edit_date(book,
				"creation-date",
				book.Metadata.document_info,
				"creation_date_string",
				"creation_date",
				dt,
				include_date
			)

		@staticmethod
		@check_book
		def source(book: ACBFBook, source: Optional[str] = None):
			pass

		@staticmethod
		@check_book
		def document_id(book: ACBFBook, id: Optional[str] = None):
			edit_optional(book, "id", book.Metadata.document_info, "document_id", id)

		@staticmethod
		@check_book
		def document_version(book: ACBFBook, version: Optional[str] = None):
			edit_optional(book, "version", book.Metadata.document_info, "document_version", version)

		class document_history:
			@staticmethod
			@check_book
			def insert(book: ACBFBook, index: int, entry: str):
				history_section = book.Metadata.document_info._info.find(f"{book.namespace}history")
				p = etree.Element(f"{book.namespace}p")
				history_section.insert(index, p)
				p.text = entry
				book.Metadata.document_info.sync_history()

			@staticmethod
			@check_book
			def append(book: ACBFBook, entry: str):
				idx = len(book.Metadata.document_info._info.findall(f"{book.namespace}history/{book.namespace}p"))
				metadata.documentinfo.document_history.insert(book, idx, entry)

			@staticmethod
			@check_book
			def edit(book: ACBFBook, index: int, text: str):
				item = book.Metadata.document_info._info.findall(f"{book.namespace}history/{book.namespace}p")[index]
				item.text = text
				book.Metadata.document_info.sync_history()

			@staticmethod
			@check_book
			def remove(book: ACBFBook, index: int):
				item = book.Metadata.document_info._info.findall(f"{book.namespace}history/{book.namespace}p")[index]
				item.clear()
				item.getparent().remove(item)
				book.Metadata.document_info.sync_history()
