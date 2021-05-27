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
from libacbf.structs import Author, DBRef, Genre
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

	au_element = etree.Element(f"{book.namespace.ACBFns}author")
	author._element = au_element
	idx = info_section.index(info_section.findall(f"{book.namespace.ACBFns}author")[-1]) + 1
	info_section.insert(idx, au_element)

	edit_author(book, section, author, author.copy())
	section.sync_authors()

def edit_author(book: ACBFBook, section, original_author: Union[Author, int], new_author: Author):
	au_list = section._info.findall(f"{book.namespace.ACBFns}author")

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
		au_element.attrib.pop("activity")
	if new_author.lang is not None:
		au_element.set("lang", str(new_author.lang))
	else:
		au_element.attrib.pop("lang")

	attrs = [
		("first-name", "first_name", 0),
		("last-name", "last_name", 1),
		("nickname", "nickname")
	]

	for i in attrs:
		element = au_element.find(book.namespace.ACBFns + i[0])
		if element is None and getattr(new_author, i[1]) is not None:
			element = etree.Element(book.namespace.ACBFns + i[0])
			if i[0] != "nickname":
				au_element.insert(i[2], element)
			else:
				if au_element.find(f"{book.namespace.ACBFns}last-name") is not None:
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
		element = au_element.find(book.namespace.ACBFns + i[0])
		if element is None and getattr(new_author, i[1]) is not None:
			element = etree.Element(book.namespace.ACBFns + i[0])
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

	au_items = info_section.findall(f"{book.namespace.ACBFns}author")
	au_items[index].clear()
	info_section.remove(au_items[index])

	section.sync_authors()

def edit_optional(book: ACBFBook, tag: str, section, attr: str, text: Optional[str] = None):
	item = section._info.find(book.namespace.ACBFns + tag)

	if text is not None:
		if item is None:
			item = etree.Element(book.namespace.ACBFns + tag)
			section._info.append(item)
		item.text = text
		setattr(section, attr, item.text)
	elif text is None and item is not None:
		item.clear()
		item.getparent().remove(item)

def edit_date(book: ACBFBook, tag: str, section, attr_s: str, attr_d: str, dt: Union[str, date], include_date: bool = True):
	item = section._info.find(book.namespace.ACBFns + tag)

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
	class data:
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

			dat_section = book._root.find(f"{book.namespace.ACBFns}data")
			if dat_section is None:
				dat_section = etree.Element(f"{book.namespace.ACBFns}data")
				book._root.append(dat_section)

			id = file_path.name
			with open(file_path, 'rb') as file:
				contents = file.read()
				content_type = magic.from_buffer(contents, True)
				data64 = str(b64encode(contents), encoding="utf-8")

			bin_element = etree.Element(f"{book.namespace.ACBFns}binary")
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
			dat_section = book._root.find(f"{book.namespace.ACBFns}data")

			if dat_section is not None:
				for i in dat_section.findall(f"{book.namespace.ACBFns}binary"):
					if i.attrib["id"] == id:
						i.clear()
						dat_section.remove(i)
						break

				if len(dat_section.findall(f"{book.namespace.ACBFns}binary")) == 0:
					dat_section.clear()
					dat_section.getparent().remove(dat_section)

				book.Data.sync_data()

	class references:
		@staticmethod
		@check_book
		def add(book: ACBFBook, id: str, paragraph: str, idx: int = -1):
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
			ref_section = book._root.find(f"{book.namespace.ACBFns}references")
			if ref_section is None:
				book._root.append(ref_section)

			ref_element = etree.Element(f"{book.namespace.ACBFns}reference")
			ref_element.set("id", id)

			p_list = re.split(r"\n", paragraph)
			for ref in p_list:
				p = f"<p>{ref}</p>"
				p_element = etree.fromstring(bytes(p, encoding="utf-8"))
				for i in list(p_element.iter()):
					i.tag = book.namespace.ACBFns + i.tag
				ref_element.append(p_element)

			if idx == -1:
				ref_section.append(ref_element)
			elif idx < 0:
				ref_section.insert(idx+1, ref_element)
			else:
				ref_section.insert(idx, ref_element)

			book.References = book.sync_references()

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
			ref_section = book._root.find(f"{book.namespace.ACBFns}references")

			if ref_section is not None:
				for i in ref_section.findall(f"{book.namespace.ACBFns}reference"):
					if i.attrib["id"] == id:
						i.clear()
						ref_section.remove(i)
						break

				if len(ref_section.findall(f"{book.namespace.ACBFns}reference")) == 0:
					ref_section.getparent().remove(ref_section)

				book.sync_references()

	class styles:
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

				title_elements = info_section.findall(f"{book.namespace.ACBFns}book-title")
				idx = info_section.index(title_elements[-1]) + 1
				found = False
				key = None

				if lang == "_":
					for i in title_elements:
						if "lang" not in i.keys():
							i.text = title
							found = True
							break
					if not found:
						t_element = etree.Element(f"{book.namespace.ACBFns}book-title")
						t_element.text = title
						info_section.insert(idx, t_element)
						found = True
				else:
					key = langcodes.standardize_tag(lang)

				if not found:
					for i in title_elements:
						if "lang" in i.keys() and langcodes.standardize_tag(i.attrib["lang"]) == key:
							i.text == title
							found = True
							break
					if not found:
						t_element = etree.Element(f"{book.namespace.ACBFns}book-title")
						t_element.set("lang", key)
						t_element.text = title
						info_section.insert(idx, t_element)
						found = True

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

				title_elements = info_section.findall(f"{book.namespace.ACBFns}book-title")

				key = None
				complete = False
				if len(title_elements) > 1:
					if lang == "_":
						for i in title_elements:
							if "lang" not in i.keys():
								i.clear()
								i.getparent().remove(i)
								complete = True
								break
					else:
						key = langcodes.standardize_tag(lang)

					if not complete:
						for i in title_elements:
							if "lang" in i.keys() and langcodes.standardize_tag(i.attrib["lang"]) == key:
								i.clear()
								i.getparent().remove(i)
								complete = True
								break

					book.Metadata.book_info.sync_book_titles()

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
				gn_elements = info_section.findall(f"{book.namespace.ACBFns}genre")

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
					gn_element = etree.Element(f"{book.namespace.ACBFns}genre")
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
				gn_elements = info_section.findall(f"{book.namespace.ACBFns}genre")

				name = None
				if type(genre) is Genres:
					name = genre.name
				elif type(genre) is Genre:
					name = genre.Genre.name

				for i in gn_elements:
					if i.text == name:
						i.clear()
						i.getparent().remove(i)
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
				annotation_elements = info_section.findall(f"{book.namespace.ACBFns}annotation")
				key = None
				idx = info_section.index(annotation_elements[-1]) + 1

				an_element = None
				if lang == "_":
					for i in annotation_elements:
						if "lang" not in i.keys():
							an_element = i
							break
					if an_element is None:
						an_element = etree.Element(f"{book.namespace.ACBFns}annotation")
						info_section.insert(idx, an_element)

				else:
					key = langcodes.standardize_tag(lang)

				if an_element is None:
					for i in annotation_elements:
						if "lang" in i.keys() and langcodes.standardize_tag(i.attrib["lang"]) == key:
							an_element = i
							break
					if an_element is None:
						an_element = etree.Element(f"{book.namespace.ACBFns}annotation")
						an_element.set("lang", key)
						info_section.insert(idx, an_element)

				for pt in text.split(r"\n"):
					p = etree.Element(f"{book.namespace.ACBFns}p")
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
				annotation_elements = info_section.findall(f"{book.namespace.ACBFns}annotation")
				an_element = None
				key = None

				if lang == "_":
					for i in annotation_elements:
						if "lang" not in i.keys():
							an_element = i
							break

				else:
					key = langcodes.standardize_tag(lang)

				if an_element is None:
					for i in annotation_elements:
						if "lang" in i.keys() and langcodes.standardize_tag(i.attrib["lang"]) == key:
							an_element = i
							break

				if an_element is None:
					return
				else:
					an_element.clear()
					an_element.getparent().remove(an_element)

				book.Metadata.book_info.sync_annotations()

		class coverpage:
			@staticmethod
			@check_book
			def edit(book: ACBFBook):
				raise NotImplementedError("TODO when making Page editor")

		# Optional
		class languagelayers:
			@staticmethod
			@check_book
			def edit(book: ACBFBook, lang: str, show: bool):
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
				ln_section = book.Metadata.book_info._info.find(f"{book.namespace.ACBFns}languages")
				if ln_section is None:
					ln_section = etree.Element(f"{book.namespace.ACBFns}languages")
					book.Metadata.book_info._info.append(ln_section)

				ln_elements = ln_section.findall(f"{book.namespace.ACBFns}text-layer")

				lang = langcodes.standardize_tag(lang)

				ln_item = None
				for i in ln_elements:
					if langcodes.standardize_tag(i.attrib["lang"]) == lang:
						ln_item = i
						break

				if ln_item is None:
					ln_item = etree.Element(f"{book.namespace.ACBFns}text-layer")
					ln_item.set("lang", lang)
					ln_section.append(ln_item)

				ln_item.set("show", str(show))

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
				ln_section = book.Metadata.book_info._info.find(f"{book.namespace.ACBFns}languages")

				if ln_section is not None:
					ln_elements = ln_section.findall(f"{book.namespace.ACBFns}text-layer")
					lang = langcodes.standardize_tag(lang)

					for i in ln_elements:
						if langcodes.standardize_tag(i.attrib["lang"]) == lang:
							i.clear()
							ln_section.remove(i)
							break

					if len(ln_section.findall(f"{book.namespace.ACBFns}text-layer")) == 0:
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
				char_section = book.Metadata.book_info._info.find(f"{book.namespace.ACBFns}characters")

				if char_section is None:
					char_section = etree.Element(f"{book.namespace.ACBFns}characters")

				char = etree.Element(f"{book.namespace.ACBFns}name")
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
				char_section = book.Metadata.book_info._info.find(f"{book.namespace.ACBFns}characters")

				if char_section is not None:
					char_elements = char_section.findall(f"{book.namespace.ACBFns}name")

					if isinstance(item, int):
						char_elements[item].clear()
						char_section.remove(char_elements[item])
					elif isinstance(item, str):
						for i in char_elements:
							if i.text == item:
								i.clear()
								char_section.remove(i)
								break

					if len(char_section.findall(f"{book.namespace.ACBFns}name")) == 0:
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
				key_elements = info_section.findall(f"{book.namespace.ACBFns}keywords")
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
						key_element = etree.Element(f"{book.namespace.ACBFns}keywords")
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
						key_element = etree.Element(f"{book.namespace.ACBFns}keywords")
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
				key_elements = book.Metadata.book_info._info.findall(f"{book.namespace.ACBFns}keywords")

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
			def edit(book: ACBFBook, title: str, sequence: str, volume: Optional[str] = None):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				title : str
					[description]
				sequence : str
					[description]
				volume : str, optional
					[description], by default None
				"""
				info_section = book.Metadata.book_info._info
				ser_items = info_section.findall(f"{book.namespace.ACBFns}sequence")
				idx = None

				if len(ser_items) > 0:
					idx = info_section.index(ser_items[-1]) + 1

				ser_element = None
				for i in ser_items:
					if i.attrib["title"] == title:
						ser_element = i
						break
				if ser_element is None:
					ser_element = etree.Element(f"{book.namespace.ACBFns}sequence")
					ser_element.set("title", title)
					if idx is not None:
						info_section.insert(idx, ser_element)
					else:
						info_section.append(ser_element)

				ser_element.text = sequence

				if volume is not None:
					ser_element.set("volume", volume)

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
				seq_items = book.Metadata.book_info._info.findall(f"{book.namespace.ACBFns}sequence")

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
				rt_items = info_section.findall(f"{book.namespace.ACBFns}content-rating")
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
					rt_element = etree.Element(f"{book.namespace.ACBFns}content-rating")
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
				rt_items = book.Metadata.book_info._info.findall(f"{book.namespace.ACBFns}sequence")

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
				db_items = info_section.findall(f"{book.namespace.ACBFns}databaseref")
				idx = None

				if len(db_items) > 0:
					idx = info_section.index(db_items[-1]) + 1

				db_element = etree.Element(f"{book.namespace.ACBFns}databaseref")
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
			def edit(book: ACBFBook, dbref: DBRef, dbname: Optional[str] = None, ref: Optional[str] = None, type: Optional[str] = None):
				"""[summary]

				Parameters
				----------
				book : ACBFBook
					[description]
				dbref : DBRef
					[description]
				dbname : str
					[description]
				ref : str
					[description]
				type : str | None, optional
					[description], by default None
				"""
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
			pub_item = book.Metadata.publisher_info._info.find(f"{book.namespace.ACBFns}publisher")
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
		pass
