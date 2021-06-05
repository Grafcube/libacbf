import re
import langcodes
import magic
import dateutil.parser
from typing import List, Optional, Union
from datetime import date
from functools import wraps
from pathlib import Path
from base64 import b64encode
from lxml import etree

from libacbf import ACBFBook
from libacbf.structs import Author, DBRef, Genre, LanguageLayer
from libacbf.constants import ArchiveTypes, Genres

def check_book(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		book: ACBFBook = kwargs["book"] if "book" in kwargs.keys() else args[0]
		if book.archive.type == ArchiveTypes.Rar:
			raise ValueError("Editing RAR Archives is not supported by this module.")
		if not book.is_open:
			raise ValueError("I/O operation on closed file.")
		func(*args, **kwargs)
	return wrapper

def add_author(book: ACBFBook, section, author: Author):
	info_section = section._info

	au_element = etree.Element(f"{book.namespace}author")
	idx = info_section.index(info_section.findall(f"{book.namespace}author")[-1]) + 1
	info_section.insert(idx, au_element)
	author._element = au_element

	edit_author(book, section, author, author.copy())
	section.sync_authors()

def edit_author(book: ACBFBook, section, original_author: Union[Author, int], new_author: Author):
	au_list = section._info.findall(f"{book.namespace}author")

	if isinstance(original_author, Author):
		if original_author._element is None:
			raise ValueError("`original_author` is not part of a book.")
		else:
			au_element = original_author._element

	elif isinstance(original_author, int):
		au_element = au_list[original_author]
		original_author = section.authors[original_author]

	if new_author.activity is not None:
		au_element.set("activity", new_author.activity.name)
	else:
		if "activity" in au_element.attrib:
			au_element.attrib.pop("activity")
	if new_author.lang is not None:
		au_element.set("lang", str(new_author.lang))
	else:
		if "lang" in au_element.attrib:
			au_element.attrib.pop("lang")

	attrs = [
		("first-name", "first_name", 0),
		("last-name", "last_name", 1),
		("nickname", "nickname")
	]

	for i in attrs:
		element = au_element.find(book.namespace + i[0])
		if element is None and getattr(new_author, i[1]) is not None:
			element = etree.Element(book.namespace + i[0])
			if i[0] != "nickname":
				au_element.insert(i[2], element)
			else:
				if au_element.find(f"{book.namespace}last-name") is not None:
					idx = 2
				else:
					idx = 0
				au_element.insert(idx, element)
			element.text = getattr(new_author, i[1])
		elif element is not None and getattr(new_author, i[1]) is not None:
			element.text = getattr(new_author, i[1])
		elif element is not None and getattr(new_author, i[1]) is None:
			element.clear()
			au_element.remove(element)

	attrs_op = [
		("middle-name", "middle_name"),
		("home-page", "home_page"),
		("email", "email")
		]

	for i in attrs_op:
		element = au_element.find(book.namespace + i[0])
		if element is None and getattr(new_author, i[1]) is not None:
			element = etree.Element(book.namespace + i[0])
			au_element.append(element)
			element.text = getattr(new_author, i[1])
		elif element is not None and getattr(new_author, i[1]) is not None:
			element.text = getattr(new_author, i[1])
		elif element is not None and getattr(new_author, i[1]) is None:
			element.clear()
			au_element.remove(element)

	section.sync_authors()

def remove_author(book: ACBFBook, section, index: int):
	info_section = section._info

	au_items = info_section.findall(f"{book.namespace}author")
	au_items[index].clear()
	info_section.remove(au_items[index])

	section.sync_authors()

def edit_optional(book: ACBFBook, tag: str, section, attr: str, text: Optional[str] = None):
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

def edit_date(book: ACBFBook, tag: str, section, attr_s: str, attr_d: str, dt: Union[str, date], include_date: bool = True):
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
	"""[summary]
	"""
	class data: # Incomplete (Archive writing)
		@staticmethod
		@check_book
		def add(book: ACBFBook, file_path: Union[str, Path], embed: bool = False):
			# TODO: Option to choose whether to embed in xml or add to archive
			"""[summary]

			Parameters
			----------
			book : ACBFBook
				[description]
			file_path : str
				[description]
			"""

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
			"""[summary]

			Parameters
			----------
			book : ACBFBook
				[description]
			id : str
				[description]
			"""
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
			"""[summary]

			Parameters
			----------
			book : ACBFBook
				[description]
			id : str
				[description]
			paragraph : str
				[description]
			idx : int, optional
				[description], by default -1
			"""
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
			"""[summary]

			Parameters
			----------
			book : ACBFBook
				[description]
			id : str
				[description]
			"""
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
			"""[summary]

			Parameters
			----------
			stylesheet : str
				[description]
			style_name : str, optional
				[description], by default "_"
			"""

			book.Styles.sync_styles()

		@staticmethod
		@check_book
		def remove(book: ACBFBook, style_name: str = "_"):
			"""[summary]

			Parameters
			----------
			book : ACBFBook
				[description]
			style_name : str, optional
				[description], by default "_"
			"""

			book.Styles.sync_styles()

class metadata:
	"""[summary]
	"""
	class bookinfo:
		class authors:
			@staticmethod
			@check_book
			def add(book: ACBFBook, author: Author):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				author : Author
					[description]
				"""
				add_author(book, book.Metadata.book_info, author)

			@staticmethod
			@check_book
			def edit(book: ACBFBook, original_author: Union[Author, int], new_author: Author):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				original_author : Union[Author, int]
					[description]
				new_author : Author
					[description]

				Raises
				------
				ValueError
					[description]
				"""
				edit_author(book, book.Metadata.book_info, original_author, new_author)

			@staticmethod
			@check_book
			def remove(book: ACBFBook, index: int):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				index : int
					[description]
				"""
				remove_author(book, book.Metadata.book_info, index)

		class title:
			@staticmethod
			@check_book
			def edit(book: ACBFBook, title: str, lang: str = "_"):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				title : str
					[description]
				lang : str, optional
					[description], by default "_"
				"""
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
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				lang : str, optional
					[description], by default "_"
				"""
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
			def edit(book: ACBFBook, genre: Union[Genre, Genres], match: Optional[int] = None):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				genre : Genre | Genres(Enum)
					[description]
				match : int, optional
					[description]

				Raises
				------
				ValueError
					[description]
				"""
				info_section = book.Metadata.book_info._info
				gn_elements = info_section.findall(f"{book.namespace}genre")

				name = None
				if type(genre) is Genres:
					name = genre.name
				elif isinstance(genre, Genre):
					name = genre.Genre.name

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

				if match is not None:
					gn_element.set("match", str(match))

				book.Metadata.book_info.sync_genres()

			@staticmethod
			@check_book
			def remove(book: ACBFBook, genre: Union[Genre, Genres]):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				genre : Union[Genre, Genres]
					[description]
				"""
				info_section = book.Metadata.book_info._info
				gn_elements = info_section.findall(f"{book.namespace}genre")

				name = None
				if type(genre) is Genres:
					name = genre.name
				elif type(genre) is Genre:
					name = genre.Genre.name

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
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				text : str
					[description]
				lang : str, optional
					[description], by default "_"
				"""
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
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				lang : str, optional
					[description], by default "_"
				"""
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
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				lang : str
					[description]
				show : bool
					[description]
				"""
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
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				layer : Union[int, LanguageLayer]
					[description]
				lang : Optional[str], optional
					[description], by default None
				show : Optional[bool], optional
					[description], by default None
				"""
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
			def remove(book: ACBFBook, lang: str):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				lang : str
					[description]
				"""
				ln_section = book.Metadata.book_info._info.find(f"{book.namespace}languages")

				if ln_section is not None:
					ln_elements = ln_section.findall(f"{book.namespace}text-layer")
					lang = langcodes.standardize_tag(lang)

					for i in ln_elements:
						if langcodes.standardize_tag(i.attrib["lang"]) == lang:
							i.clear()
							ln_section.remove(i)
							break

					if len(ln_section.findall(f"{book.namespace}text-layer")) == 0:
						ln_section.clear()
						ln_section.getparent().remove(ln_section)

					book.Metadata.book_info.sync_languages()

		class characters:
			@staticmethod
			@check_book
			def add(book: ACBFBook, name: str):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				name : str
					[description]
				"""
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
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				item : str | int
					[description]
				"""
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
			def edit(book: ACBFBook, keywords: List[str], lang: str = "_"):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				keywords : List[str]
					[description]
				lang : str, optional
					[description], by default "_"
				"""
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
					if key_element is None:
						key_element = etree.Element(f"{book.namespace}keywords")
						if idx is not None:
							info_section.insert(idx, key_element)
						else:
							info_section.append(key_element)
				else:
					lang = langcodes.standardize_tag(lang)
					for i in key_elements:
						if "lang" in i.keys() and langcodes.standardize_tag(i.attrib["lang"]) == lang:
							key_element = i
							break
					if key_element is None:
						key_element = etree.Element(f"{book.namespace}keywords")
						key_element.set("lang", lang)
						if idx is not None:
							info_section.insert(idx, key_element)
						else:
							info_section.append(key_element)

				key_element.text = ", ".join(keywords)

				book.Metadata.book_info.sync_keywords()

			@staticmethod
			@check_book
			def remove(book: ACBFBook, lang: str = "_"):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				lang : str, optional
					[description], by default "_"
				"""
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
			def edit(book: ACBFBook, title: str, sequence: Optional[str] = None, volume: Optional[str] = None):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				title : str
					[description]
				sequence : Optional[str], optional
					[description], by default None
				volume : Optional[str], optional
					[description], by default None
				"""
				info_section = book.Metadata.book_info._info
				ser_items = info_section.findall(f"{book.namespace}sequence")
				idx = None

				if len(ser_items) > 0:
					idx = info_section.index(ser_items[-1]) + 1

				ser_element = None
				for i in ser_items:
					if i.attrib["title"] == title:
						ser_element = i
						break
				if ser_element is None:
					ser_element = etree.Element(f"{book.namespace}sequence")
					ser_element.set("title", title)
					if idx is not None:
						info_section.insert(idx, ser_element)
					else:
						info_section.append(ser_element)

				if sequence is not None:
					ser_element.text = sequence

				if volume is not None:
					ser_element.set("volume", volume)
				else:
					if "volume" in ser_element.keys():
						ser_element.attrib.pop("volume")

				book.Metadata.book_info.sync_series()

			def remove(book: ACBFBook, title: str):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				title : str
					[description]
				"""
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
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				rating : str
					[description]
				type : str, optional
					[description], by default "_"
				"""
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
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				type : str, optional
					[description], by default "_"
				"""
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
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				dbname : str
					[description]
				ref : str
					[description]
				type : str | None, optional
					[description], by default None
				"""
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
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				dbref : int | DBRef
					[description]
				dbname : str
					[description]
				ref : str
					[description]
				type : str | None, optional
					[description], by default None
				"""
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
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				dbref : DBRef
					[description]
				"""
				dbref._element.clear()
				dbref._element.getparent().remove(dbref._element)
				book.Metadata.book_info.sync_database_ref()

	class publishinfo:
		@staticmethod
		@check_book
		def publisher(book: ACBFBook, name: str):
			"""[summary]

			Parameters
			----------
			book : ACBFBook
				[description]
			name : str
				[description]
			"""
			pub_item = book.Metadata.publisher_info._info.find(f"{book.namespace}publisher")
			pub_item.text = name
			book.Metadata.publisher_info.publisher = pub_item.text

		@staticmethod
		@check_book
		def publish_date(book: ACBFBook, dt: Union[str, date], include_date: bool = True):
			"""[summary]

			Parameters
			----------
			book : ACBFBook
				[description]
			dt : str | date
				[description]
			include_date : bool, optional
				[description], by default True
			"""
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
			"""[summary]

			Parameters
			----------
			book : ACBFBook
				[description]
			city : str
				[description]
			"""
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
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				author : Author
					[description]
				"""
				add_author(book, book.Metadata.document_info, author)

			@staticmethod
			@check_book
			def edit(book: ACBFBook, original_author: Union[Author, int], new_author: Author):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				original_author : Union[Author, int]
					[description]
				new_author : Author
					[description]

				Raises
				------
				ValueError
					[description]
				"""
				edit_author(book, book.Metadata.document_info, original_author, new_author)

			@staticmethod
			@check_book
			def remove(book: ACBFBook, index: int):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				index : int
					[description]
				"""
				remove_author(book, book.Metadata.document_info, index)

		@staticmethod
		@check_book
		def creation_date(book: ACBFBook, dt: Union[str, date], include_date: bool = True):
			"""[summary]

			Parameters
			----------
			book : ACBFBook
				[description]
			dt : Union[str, date]
				[description]
			include_date : bool, optional
				[description], by default True
			"""
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
			"""[summary]

			Parameters
			----------
			book : ACBFBook
				[description]
			source : Optional[str], optional
				[description], by default None
			"""
			pass

		@staticmethod
		@check_book
		def document_id(book: ACBFBook, id: Optional[str] = None):
			"""[summary]

			Parameters
			----------
			book : ACBFBook
				[description]
			id : Optional[str], optional
				[description], by default None
			"""
			edit_optional(book, "id", book.Metadata.document_info, "document_id", id)

		@staticmethod
		@check_book
		def document_version(book: ACBFBook, version: Optional[str] = None):
			"""[summary]

			Parameters
			----------
			book : ACBFBook
				[description]
			version : Optional[str], optional
				[description], by default None
			"""
			edit_optional(book, "version", book.Metadata.document_info, "document_version", version)

		class document_history:
			@staticmethod
			@check_book
			def insert(book: ACBFBook, index: int, entry: str):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				index : int
					[description]
				entry : str
					[description]
				"""
				history_section = book.Metadata.document_info._info.find(f"{book.namespace}history")
				p = etree.Element(f"{book.namespace}p")
				history_section.insert(index, p)
				p.text = entry
				book.Metadata.document_info.sync_history()

			@staticmethod
			@check_book
			def append(book: ACBFBook, entry: str):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				entry : str
					[description]
				"""
				idx = len(book.Metadata.document_info._info.findall(f"{book.namespace}history/{book.namespace}p"))
				metadata.documentinfo.document_history.insert(book, idx, entry)

			@staticmethod
			@check_book
			def edit(book: ACBFBook, index: int, text: str):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				index : int
					[description]
				text : str
					[description]
				"""
				item = book.Metadata.document_info._info.findall(f"{book.namespace}history/{book.namespace}p")[index]
				item.text = text
				book.Metadata.document_info.sync_history()

			@staticmethod
			@check_book
			def remove(book: ACBFBook, index: int):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				index : int
					[description]
				"""
				item = book.Metadata.document_info._info.findall(f"{book.namespace}history/{book.namespace}p")[index]
				item.clear()
				item.getparent().remove(item)
				book.Metadata.document_info.sync_history()
