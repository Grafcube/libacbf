import re
import langcodes
import magic
from typing import Union
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
	@staticmethod
	@check_book
	def add_data(book: ACBFBook, file_path: Union[str, Path], embed: bool = False):
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
	def remove_data(book: ACBFBook, id: str):
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

	@staticmethod
	@check_book
	def edit_styles(book: ACBFBook, stylesheet: str, style_name: str = "_"):
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
	def remove_style(book: ACBFBook, style_name: str = "_"):
		"""[summary]

		Parameters
		----------
		book : ACBFBook
			[description]
		style_name : str, optional
			[description], by default "_"
		"""

		book.Styles.sync_styles()

	@staticmethod
	@check_book
	def add_reference(book: ACBFBook, id: str, paragraph: str, idx: int = -1):
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
	def remove_reference(book: ACBFBook, id: str):
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

class book_metadata:
	"""[summary]
	"""
	@staticmethod
	@check_book
	def add_book_author(book: ACBFBook, author: Author):
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
	def edit_book_author(book: ACBFBook, original_author: Union[Author, int], new_author: Author):
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

		if type(original_author) is Author:
			if original_author._element is None:
				raise ValueError("`original_author` is not part of the book.")
			else:
				au_element = original_author._element

		elif type(original_author) is int:
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
	def remove_book_author(book: ACBFBook, index: int):
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

	@staticmethod
	@check_book
	def edit_book_title(book: ACBFBook, title: str, lang: str = "_"):
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
				if key == langcodes.standardize_tag(i.attrib["lang"]):
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
	def remove_book_title(book: ACBFBook, lang: str = "_"):
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
					if key == langcodes.standardize_tag(i.attrib["lang"]):
						i.clear()
						i.getparent().remove(i)
						complete = True
						break

			book.Metadata.book_info.sync_book_titles()

	@staticmethod
	@check_book
	def add_genre(book: ACBFBook, genre: Union[Genre, Genres]):
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
		idx = info_section.index(gn_elements[-1]) + 1

		name = None
		match = None

		if type(genre) is Genres:
			if genre.name in book.Metadata.book_info.genres.keys():
				return
			else:
				name = genre.name
		elif type(genre) is Genre:
			if genre.Genre.name in book.Metadata.book_info.genres.keys():
				if genre.Match is not None:
					edit_genre_match(genre.Match, genre)
					return
				else:
					return
			else:
				name = genre.Genre.name
				match = genre.Match

		gn_element = etree.Element(f"{book.namespace.ACBFns}genre")
		gn_element.text = name
		if match is not None:
			gn_element.set("match", str(match))
		info_section.insert(idx, gn_element)

		book.Metadata.book_info.sync_genres()

	@staticmethod
	@check_book
	def edit_genre_match(book: ACBFBook, match: int, genre: Union[Genre, Genres]):
		"""[summary]

		Parameters
		----------
		book : ACBFBook
			[description]
		match : int
			[description]
		genre : Union[Genre, Genres]
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
			if genre.name not in book.Metadata.book_info.genres.keys():
				raise ValueError("The specified Genre was not found.")
			else:
				name = genre.name
		elif type(genre) is Genre:
			if genre.Genre.name not in book.Metadata.book_info.genres.keys():
				raise ValueError("The specified Genre was not found.")
			else:
				name = genre.Genre.name

		for i in gn_elements:
			if i.text == name:
				gn_element = i
				break
		gn_element.set("match", str(match))

		book.Metadata.book_info.sync_genres()

	@staticmethod
	@check_book
	def remove_genre(book: ACBFBook, genre: Union[Genre, Genres]):
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

	@staticmethod
	@check_book
	def edit_annotation(book: ACBFBook, text: str, lang: str = "_"):
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
		an_element = None
		key = None
		idx = info_section.index(annotation_elements[-1]) + 1

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
				if langcodes.standardize_tag(i.attrib["lang"]) == key:
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
	def remove_annotation(book: ACBFBook, lang: str = "_"):
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
				if langcodes.standardize_tag(i.attrib["lang"]) == key:
					an_element = i
					break

		if an_element is None:
			return
		else:
			an_element.clear()
			an_element.getparent().remove(an_element)

		book.Metadata.book_info.sync_annotations()
