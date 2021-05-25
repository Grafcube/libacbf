import re
import langcodes
import magic
from typing import List, Optional, Union
from functools import wraps
from pathlib import Path
from base64 import b64encode
from lxml import etree

from libacbf import ACBFBook
from libacbf.structs import Author, Genre
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

def _check_data_section(book: ACBFBook, create: bool = True):
	dat_section = book._root.find(f"{book.namespace.ACBFns}data")
	if dat_section is None and create:
		ref_section = book._root.find(f"{book.namespace.ACBFns}references")
		if ref_section is None:
			idx = book._root.index(book._root.find(f"{book.namespace.ACBFns}body"))
		else:
			idx = book._root.index(ref_section)
		dat_section = etree.Element(f"{book.namespace.ACBFns}data")
		book._root.insert(idx+1, dat_section)
	return dat_section

def _check_reference_section(book: ACBFBook, create: bool = True):
	ref_section = book._root.find(f"{book.namespace.ACBFns}references")
	if ref_section is None and create:
		idx = book._root.index(book._root.find(f"{book.namespace.ACBFns}body"))
		ref_section = etree.Element(f"{book.namespace.ACBFns}references")
		book._root.insert(idx+1, ref_section)
	return ref_section

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

			dat_section = _check_data_section(book)

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
			dat_section = _check_data_section(book, False)
			if dat_section is not None:
				for i in dat_section.findall(f"{book.namespace.ACBFns}binary"):
					if i.attrib["id"] == id:
						i.clear()
						i.getparent().remove(i)
						break

				book.Data.sync_data()

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
			ref_section = _check_reference_section(book)

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
			ref_section = _check_reference_section(book, False)
			if ref_section is not None:
				for i in ref_section.findall(f"{book.namespace.ACBFns}reference"):
					if i.attrib["id"] == id:
						i.clear()
						i.getparent().remove(i)
						break

				book.References = book.sync_references()

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
				info_section = book.Metadata.book_info._info

				au_element = etree.Element(f"{book.namespace.ACBFns}author")

				if author.activity is not None:
					au_element.set("activity", author.activity.name)
				if author.lang is not None:
					au_element.set("lang", str(author.lang))

				if author.first_name is not None:
					element = etree.Element(f"{book.namespace.ACBFns}first-name")
					element.text = author.first_name
					au_element.append(element)
				if author.last_name is not None:
					element = etree.Element(f"{book.namespace.ACBFns}last-name")
					element.text = author.last_name
					au_element.append(element)
				if author.nickname is not None:
					element = etree.Element(f"{book.namespace.ACBFns}nickname")
					element.text = author.nickname
					au_element.append(element)
				if author.middle_name is not None:
					element = etree.Element(f"{book.namespace.ACBFns}middle-name")
					element.text = author.middle_name
					au_element.append(element)
				if author.home_page is not None:
					element = etree.Element(f"{book.namespace.ACBFns}home-page")
					element.text = author.home_page
					au_element.append(element)
				if author.email is not None:
					element = etree.Element(f"{book.namespace.ACBFns}email")
					element.text = author.email
					au_element.append(element)

				last_au_idx = 0
				if len(info_section.findall(f"{book.namespace.ACBFns}author")) > 0:
					last_au_idx = info_section.index(info_section.findall(f"{book.namespace.ACBFns}author")[-1])
				info_section.insert(last_au_idx+1, au_element)

				book.Metadata.book_info.sync_authors()

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
				au_list = book.Metadata.book_info._info.findall(f"{book.namespace.ACBFns}author")

				if isinstance(original_author, Author):
					if original_author._element is None:
						raise ValueError("`original_author` is not part of the book.")
					else:
						au_element = original_author._element

				elif isinstance(original_author, int):
					au_element = au_list[original_author]
					original_author = book.Metadata.book_info.authors[original_author]

				if new_author.activity is not None:
					au_element.set("activity", new_author.activity.name)
				if new_author.lang is not None:
					au_element.set("lang", str(new_author.lang))

				if new_author.first_name is not None:
					element = au_element.find(f"{book.namespace.ACBFns}first-name")
					if element is None:
						element = etree.Element(f"{book.namespace.ACBFns}first-name")
						au_element.insert(0, element)
					element.text = new_author.first_name

				if new_author.last_name is not None:
					element = au_element.find(f"{book.namespace.ACBFns}last-name")
					if element is None:
						element = etree.Element(f"{book.namespace.ACBFns}last-name")
						if au_element.find(f"{book.namespace.ACBFns}middle-name") is not None:
							au_element.insert(2, element)
						else:
							au_element.insert(1, element)
					element.text = new_author.last_name

				if new_author.nickname is not None:
					element = au_element.find(f"{book.namespace.ACBFns}nickname")
					if element is None:
						element = etree.Element(f"{book.namespace.ACBFns}nickname")
						if au_element.find(f"{book.namespace.ACBFns}last-name") is not None:
							if au_element.find(f"{book.namespace.ACBFns}middle-name"):
								idx = 3
							else:
								idx = 2
						elif au_element.find(f"{book.namespace.ACBFns}middle-name") is not None:
							idx = 1
						else:
							idx = 0
						au_element.insert(idx, element)
					element.text = new_author.nickname

				if new_author.middle_name is not None:
					element = au_element.find(f"{book.namespace.ACBFns}middle-name")
					if element is None:
						element = etree.Element(f"{book.namespace.ACBFns}middle-name")
						if au_element.find(f"{book.namespace.ACBFns}first-name") is not None:
							au_element.insert(1, element)
						else:
							au_element.insert(0, element)
					element.text = new_author.middle_name

				if new_author.home_page is not None:
					element = au_element.find(f"{book.namespace.ACBFns}home-page")
					if element is None:
						element = etree.Element(f"{book.namespace.ACBFns}home-page")
						au_element.append(element)
					element.text = new_author.home_page

				if new_author.email is not None:
					element = au_element.find(f"{book.namespace.ACBFns}email")
					if element is None:
						element = etree.Element(f"{book.namespace.ACBFns}email")
						au_element.append(element)
					element.text = new_author.email

				book.Metadata.book_info.sync_authors()

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
				info_section = book.Metadata.book_info._info

				au_items = info_section.findall(f"{book.namespace.ACBFns}author")
				au_items[index].clear()
				au_items[index].getparent().remove(au_items[index])

				book.Metadata.book_info.sync_authors()

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

		class language_layers:
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
				ln_elements = ln_section.findall(f"{book.namespace.ACBFns}text-layer")
				lang = langcodes.standardize_tag(lang)

				for i in ln_elements:
					if langcodes.standardize_tag(i.attrib["lang"]) == lang:
						i.clear()
						ln_section.remove(i)
						book.Metadata.book_info.sync_languages()
						break

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
				char_elements = char_section.findall(f"{book.namespace.ACBFns}name")

				if isinstance(item, int):
					char_elements[item].clear()
					char_section.remove(char_elements[item])
					book.Metadata.book_info.sync_characters()
				elif isinstance(item, str):
					for i in char_elements:
						if i.text == item:
							i.clear()
							char_section.remove(i)
							book.Metadata.book_info.sync_characters()
							break

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

				if len(key_elements) > 0:
					idx = info_section.index(key_elements[-1]) + 1
				else:
					idx = info_section.index(info_section.find(f"{book.namespace.ACBFns}coverpage")) + 1

				key_element = None
				if lang == "_":
					for i in key_elements:
						if "lang" not in i.keys():
							key_element = i
							break
					if key_element is None:
						key_element = etree.Element(f"{book.namespace.ACBFns}keywords")
						info_section.insert(idx, key_element)
				else:
					lang = langcodes.standardize_tag(lang)
					for i in key_elements:
						if "lang" in i.keys() and langcodes.standardize_tag(i.attrib["lang"]) == lang:
							key_element = i
							break
					if key_element is None:
						key_element = etree.Element(f"{book.namespace.ACBFns}keywords")
						key_element.set("lang", lang)
						info_section.insert(idx, key_element)

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

				if len(ser_items) > 0:
					idx = info_section.index(ser_items[-1]) + 1
				else:
					idx = info_section.index(info_section.find(f"{book.namespace.ACBFns}coverpage")) + 1

				ser_element = None
				for i in ser_items:
					if i.attrib["title"] == title:
						ser_element = i
						break
				if ser_element is None:
					ser_element = etree.Element(f"{book.namespace.ACBFns}sequence")
					ser_element.set("title", title)
					info_section.insert(idx, ser_element)

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

		class content_rating:
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

				if len(rt_items) > 0:
					idx = info_section.index(rt_items[-1]) + 1
				else:
					idx = info_section.index(info_section.find(f"{book.namespace.ACBFns}coverpage")) + 1

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
					info_section.insert(idx, rt_element)
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
