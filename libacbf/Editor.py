from typing import Union
from re import split
from pathlib import Path
from base64 import b64encode
from langcodes import Language, standardize_tag
from magic import from_buffer
from lxml import etree
from libacbf.ACBFBook import ACBFBook, get_references
from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.Structs import Author, Genre
from libacbf.Constants import BookNamespace, Genres

class BookManager:
	"""
	docstring
	"""
	def __init__(self, book: ACBFBook):
		if book.is_open:
			self.book = book
		else:
			raise ValueError("I/O operation on closed file.")

	def _check_reference_section(self, create: bool = True):
		ref_section = self.book.root.find(f"{self.book.namespace.ACBFns}references")
		if ref_section is None and create:
			idx = self.book.root.index(self.book.root.find(f"{self.book.namespace.ACBFns}body"))
			ref_section = etree.Element(f"{self.book.namespace.ACBFns}references")
			self.book.root.insert(idx+1, ref_section)
		return ref_section

	def _check_data_section(self, create: bool = True):
		dat_section = self.book.root.find(f"{self.book.namespace.ACBFns}data")
		if dat_section is None and create:
			ref_section = self.book.root.find(f"{self.book.namespace.ACBFns}references")
			if ref_section is None:
				idx = self.book.root.index(self.book.root.find(f"{self.book.namespace.ACBFns}body"))
			else:
				idx = self.book.root.index(ref_section)
			dat_section = etree.Element(f"{self.book.namespace.ACBFns}data")
			self.book.root.insert(idx+1, dat_section)
		return dat_section

	def add_reference(self, id: str, paragraph: str, idx: int = -1):
		"""
		docstring
		"""
		ref_section = self._check_reference_section()

		ref_element = etree.Element(f"{self.book.namespace.ACBFns}reference")
		ref_element.set("id", id)

		p_list = split(r"\n", paragraph)
		for ref in p_list:
			p = f"<p>{ref}</p>"
			p_element = etree.fromstring(bytes(p, encoding="utf-8"))
			for i in list(p_element.iter()):
				i.tag = self.book.namespace.ACBFns + i.tag
			ref_element.append(p_element)

		if idx == -1:
			ref_section.append(ref_element)
		elif idx < 0:
			ref_section.insert(idx+1, ref_element)
		else:
			ref_section.insert(idx, ref_element)

		self.book.References = get_references(self.book.root.find(f"{self.book.namespace.ACBFns}references"), self.book.namespace)

	def remove_reference(self, id: str):
		"""
		docstring
		"""
		ref_section = self._check_reference_section(False)
		if ref_section is not None:
			for i in ref_section.findall(f"{self.book.namespace.ACBFns}reference"):
				if i.attrib["id"] == id:
					i.clear()
					i.getparent().remove(i)
					break

			self.book.References = get_references(self.book.root.find(f"{self.book.namespace.ACBFns}references"), self.book.namespace)

	def add_data(self, file_path: str):
		# TODO: Option to choose whether to embed in xml or add to archive
		"""
		docstring
		"""
		dat_section = self._check_data_section()

		dat_path = Path(file_path)

		id = dat_path.name
		with open(file_path, 'rb') as file:
			contents = file.read()
			content_type = from_buffer(contents, True)
			data64 = str(b64encode(contents), encoding="utf-8")

		bin_element = etree.Element(f"{self.book.namespace.ACBFns}binary")
		bin_element.set("id", id)
		bin_element.set("content-type", content_type)
		bin_element.text = data64

		dat_section.append(bin_element)
		self.book.Data.sync_data()

	def remove_data(self, id: str):
		"""
		docstring
		"""
		dat_section = self._check_data_section(False)
		if dat_section is not None:
			for i in dat_section.findall(f"{self.book.namespace.ACBFns}binary"):
				if i.attrib["id"] == id:
					i.clear()
					i.getparent().remove(i)
					break

			self.book.Data.sync_data()

	def edit_styles(self, stylesheet: str, file_name: str = "_"):
		"""
		docstring
		"""
		pass

class MetadataManager:
	"""
	docstring
	"""
	def __init__(self, book: ACBFBook):
		if book.is_open:
			self.metadata: ACBFMetadata = book.Metadata
			self.ns: BookNamespace = book.namespace
		else:
			raise ValueError("I/O operation on closed file.")

	def add_book_author(self, author: Author):
		"""
		docstring
		"""
		info_section = self.metadata.book_info._info

		au_element = etree.Element(f"{self.ns.ACBFns}author")

		if author.activity is not None:
			au_element.set("activity", author.activity.name)
		if author.lang is not None:
			au_element.set("lang", str(author.lang))

		if author.first_name is not None:
			element = etree.Element(f"{self.ns.ACBFns}first-name")
			element.text = author.first_name
			au_element.append(element)
		if author.last_name is not None:
			element = etree.Element(f"{self.ns.ACBFns}last-name")
			element.text = author.last_name
			au_element.append(element)
		if author.nickname is not None:
			element = etree.Element(f"{self.ns.ACBFns}nickname")
			element.text = author.nickname
			au_element.append(element)
		if author.middle_name is not None:
			element = etree.Element(f"{self.ns.ACBFns}middle-name")
			element.text = author.middle_name
			au_element.append(element)
		if author.home_page is not None:
			element = etree.Element(f"{self.ns.ACBFns}home-page")
			element.text = author.home_page
			au_element.append(element)
		if author.email is not None:
			element = etree.Element(f"{self.ns.ACBFns}email")
			element.text = author.email
			au_element.append(element)

		last_au_idx = 0
		if len(info_section.findall(f"{self.ns.ACBFns}author")) > 0:
			last_au_idx = info_section.index(info_section.findall(f"{self.ns.ACBFns}author")[-1])
		info_section.insert(last_au_idx+1, au_element)

		self.metadata.book_info.sync_authors()

	def edit_book_author(self, original_author: Union[Author, int], new_author: Author):
		au_list = self.metadata.book_info._info.findall(f"{self.ns.ACBFns}author")

		if type(original_author) is Author:
			if original_author._element is None:
				raise ValueError("`original_author` is not part of the book.")
			else:
				au_element = original_author._element

		elif type(original_author) is int:
			au_element = au_list[original_author]
			original_author = self.metadata.book_info.authors[original_author]

		if new_author.activity is not None:
			au_element.set("activity", new_author.activity.name)
		if new_author.lang is not None:
			au_element.set("lang", str(new_author.lang))

		if new_author.first_name is not None:
			element = au_element.find(f"{self.ns.ACBFns}first-name")
			if element is None:
				element = etree.Element(f"{self.ns.ACBFns}first-name")
				au_element.insert(0, element)
			element.text = new_author.first_name

		if new_author.last_name is not None:
			element = au_element.find(f"{self.ns.ACBFns}last-name")
			if element is None:
				element = etree.Element(f"{self.ns.ACBFns}last-name")
				if au_element.find(f"{self.ns.ACBFns}middle-name") is not None:
					au_element.insert(2, element)
				else:
					au_element.insert(1, element)
			element.text = new_author.last_name

		if new_author.nickname is not None:
			element = au_element.find(f"{self.ns.ACBFns}nickname")
			if element is None:
				element = etree.Element(f"{self.ns.ACBFns}nickname")
				if au_element.find(f"{self.ns.ACBFns}last-name") is not None:
					if au_element.find(f"{self.ns.ACBFns}middle-name"):
						idx = 3
					else:
						idx = 2
				elif au_element.find(f"{self.ns.ACBFns}middle-name") is not None:
					idx = 1
				else:
					idx = 0
				au_element.insert(idx, element)
			element.text = new_author.nickname

		if new_author.middle_name is not None:
			element = au_element.find(f"{self.ns.ACBFns}middle-name")
			if element is None:
				element = etree.Element(f"{self.ns.ACBFns}middle-name")
				if au_element.find(f"{self.ns.ACBFns}first-name") is not None:
					au_element.insert(1, element)
				else:
					au_element.insert(0, element)
			element.text = new_author.middle_name

		if new_author.home_page is not None:
			element = au_element.find(f"{self.ns.ACBFns}home-page")
			if element is None:
				element = etree.Element(f"{self.ns.ACBFns}home-page")
				au_element.append(element)
			element.text = new_author.home_page

		if new_author.email is not None:
			element = au_element.find(f"{self.ns.ACBFns}email")
			if element is None:
				element = etree.Element(f"{self.ns.ACBFns}email")
				au_element.append(element)
			element.text = new_author.email

		self.metadata.book_info.sync_authors()

	def remove_book_author(self, index: int):
		"""
		docstring
		"""
		info_section = self.metadata.book_info._info

		au_items = info_section.findall(f"{self.ns.ACBFns}author")
		au_items[index].clear()
		au_items[index].getparent().remove(au_items[index])

		self.metadata.book_info.sync_authors()

	def edit_book_title(self, title: str, lang: Union[str, Language] = "_"):
		"""
		docstring
		"""
		info_section = self.metadata.book_info._info

		title_elements = info_section.findall(f"{self.ns.ACBFns}book-title")
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
				t_element = etree.Element(f"{self.ns.ACBFns}book-title")
				t_element.text = title
				info_section.insert(idx, t_element)
				found = True

		elif type(lang) is Language:
			key = str(lang)
		elif type(lang) is str:
			key = standardize_tag(lang)

		if not found:
			for i in title_elements:
				if key == standardize_tag(i.attrib["lang"]):
					i.text == title
					found = True
					break
			if not found:
				t_element = etree.Element(f"{self.ns.ACBFns}book-title")
				t_element.set("lang", key)
				t_element.text = title
				info_section.insert(idx, t_element)
				found = True

		self.metadata.book_info.sync_book_titles()

	def remove_book_title(self, lang: Union[str, Language] = "_"):
		"""
		docstring
		"""
		info_section = self.metadata.book_info._info

		title_elements = info_section.findall(f"{self.ns.ACBFns}book-title")

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
			elif type(lang) is Language:
				key = str(lang)
			elif type(lang) is str:
				key = standardize_tag(lang)

			if not complete:
				for i in title_elements:
					if key == standardize_tag(i.attrib["lang"]):
						i.clear()
						i.getparent().remove(i)
						complete = True
						break

			self.metadata.book_info.sync_book_titles()

	def add_genre(self, genre: Union[Genre, Genres]):
		"""
		docstring
		"""
		info_section = self.metadata.book_info._info

		gn_elements = info_section.findall(f"{self.ns.ACBFns}genre")
		idx = info_section.index(gn_elements[-1]) + 1

		name = None
		match = None

		if type(genre) is Genres:
			if genre.name in self.metadata.book_info.genres.keys():
				return
			else:
				name = genre.name
		elif type(genre) is Genre:
			if genre.Genre.name in self.metadata.book_info.genres.keys():
				if genre.Match is not None:
					self.edit_genre_match(genre.Match, genre)
					return
				else:
					return
			else:
				name = genre.Genre.name
				match = genre.Match

		gn_element = etree.Element(f"{self.ns.ACBFns}genre")
		gn_element.text = name
		if match is not None:
			gn_element.set("match", str(match))
		info_section.insert(idx, gn_element)

		self.metadata.book_info.sync_genres()

	def edit_genre_match(self, match: int, genre: Union[Genre, Genres]):
		"""
		docstring
		"""
		info_section = self.metadata.book_info._info
		gn_elements = info_section.findall(f"{self.ns.ACBFns}genre")
		name = None

		if type(genre) is Genres:
			if genre.name not in self.metadata.book_info.genres.keys():
				raise ValueError("The specified Genre was not found.")
			else:
				name = genre.name
		elif type(genre) is Genre:
			if genre.Genre.name not in self.metadata.book_info.genres.keys():
				raise ValueError("The specified Genre was not found.")
			else:
				name = genre.Genre.name

		for i in gn_elements:
			if i.text == name:
				gn_element = i
				break
		gn_element.set("match", str(match))

		self.metadata.book_info.sync_genres()

	def remove_genre(self, genre: Union[Genre, Genres]):
		"""
		docstring
		"""
		info_section = self.metadata.book_info._info
		gn_elements = info_section.findall(f"{self.ns.ACBFns}genre")
		name = None

		if type(genre) is Genres:
			name = genre.name
		elif type(genre) is Genre:
			name = genre.Genre.name

		for i in gn_elements:
			if i.text == name:
				i.clear()
				i.getparent().remove(i)
				self.metadata.book_info.sync_genres()
				break

	def edit_annotation(self, text: str, lang: Union[str, Language] = "_"):
		"""
		docstring
		"""
		info_section = self.metadata.book_info._info

		annotation_elements = info_section.findall(f"{self.ns.ACBFns}annotation")
		an_element = None
		key = None
		idx = info_section.index(annotation_elements[-1]) + 1

		if lang == "_":
			for i in annotation_elements:
				if "lang" not in i.keys():
					an_element = i
					break
			if an_element is None:
				an_element = etree.Element(f"{self.ns.ACBFns}annotation")
				info_section.insert(idx, an_element)

		elif type(lang) is Language:
			key = str(lang)
		elif type(lang) is str:
			key = standardize_tag(lang)

		if an_element is None:
			for i in annotation_elements:
				if standardize_tag(i.attrib["lang"]) == key:
					an_element = i
					break
			if an_element is None:
				an_element = etree.Element(f"{self.ns.ACBFns}annotation")
				an_element.set("lang", key)
				info_section.insert(idx, an_element)

		for pt in text.split(r"\n"):
			p = etree.Element(f"{self.ns.ACBFns}p")
			p.text = pt
			an_element.append(p)

		self.metadata.book_info.sync_annotations()

	def remove_annotation(self, lang: Union[str, Language] = "_"):
		"""
		docstring
		"""
		info_section = self.metadata.book_info._info
		annotation_elements = info_section.findall(f"{self.ns.ACBFns}annotation")
		an_element = None
		key = None

		if lang == "_":
			for i in annotation_elements:
				if "lang" not in i.keys():
					an_element = i
					break

		elif type(lang) is Language:
			key = str(lang)
		elif type(lang) is str:
			key = standardize_tag(lang)

		if an_element is None:
			for i in annotation_elements:
				if standardize_tag(i.attrib["lang"]) == key:
					an_element = i
					break

		if an_element is None:
			return
		else:
			an_element.clear()
			an_element.getparent().remove(an_element)

		self.metadata.book_info.sync_annotations()
