from __future__ import annotations

import re
import langcodes
import dateutil.parser
from typing import TYPE_CHECKING, Optional, Union
from datetime import date
from lxml import etree

if TYPE_CHECKING:
	from libacbf import ACBFBook

import libacbf.structs as structs
from libacbf.constants import ArchiveTypes, AuthorActivities
from libacbf.metadata import BookInfo, PublishInfo, DocumentInfo
from libacbf.exceptions import EditRARArchiveError

def check_book(book: ACBFBook):
	if book.mode != 'r':
		raise ValueError("Cannot edit read only book.")
	if not book.is_open:
		raise ValueError("Cannot edit closed book.")
	if book.archive is not None and book.archive.type == ArchiveTypes.Rar:
		raise EditRARArchiveError

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

def edit_optional(book: ACBFBook, tag: str, section: Union[BookInfo, PublishInfo, DocumentInfo], attr: str, text: Optional[str] = None):
	item = section._info.find(book._namespace + tag)

	if text is not None:
		if item is None:
			item = etree.Element(book._namespace + tag)
			section._info.append(item)
		item.text = text
		setattr(section, attr, item.text)
	elif text is None and item is not None:
		item.clear()
		item.getparent().remove(item)

def edit_date(book: ACBFBook, tag: str, section: Union[BookInfo, PublishInfo, DocumentInfo], attr_s: str, attr_d: str, dt: Union[str, date], include_date: bool = True):
	item = section._info.find(book._namespace + tag)

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

def edit_coverpage(book: ACBFBook):
	raise NotImplementedError

class metadata:
	class publishinfo:
		@staticmethod
		def publisher(book: ACBFBook, name: str):
			pub_item = book.Metadata.publisher_info._info.find(f"{book._namespace}publisher")
			pub_item.text = name
			book.Metadata.publisher_info.publisher = pub_item.text

		@staticmethod
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
		def publish_city(book: ACBFBook, city: Optional[str] = None):
			edit_optional(book, "city", book.Metadata.publisher_info, "publish_city", city)

		@staticmethod
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
			def add(book: ACBFBook, author: structs.Author):
				add_author(book, book.Metadata.document_info, author)

			@staticmethod
			def edit(book: ACBFBook, author: Union[structs.Author, int], **attributes):
				edit_author(book, book.Metadata.document_info, author, **attributes)

			@staticmethod
			def remove(book: ACBFBook, author: Union[int, structs.Author]):
				remove_author(book, book.Metadata.document_info, author)

		@staticmethod
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
		def source(book: ACBFBook, source: Optional[str] = None):
			src_section = book.Metadata.document_info._info.find(f"{book._namespace}source")

			if source is not None:
				if src_section is None:
					src_section = etree.Element(f"{book._namespace}source")
					book.Metadata.document_info._info.append(src_section)
				src_section.clear()
				for i in re.split('\n', source):
					p = etree.Element(f"{book._namespace}p")
					src_section.append(p)
					p.text = i
			else:
				if src_section is not None:
					src_section.clear()
					src_section.getparent().remove(src_section)

		@staticmethod
		def document_id(book: ACBFBook, id: Optional[str] = None):
			edit_optional(book, "id", book.Metadata.document_info, "document_id", id)

		@staticmethod
		def document_version(book: ACBFBook, version: Optional[str] = None):
			edit_optional(book, "version", book.Metadata.document_info, "document_version", version)

		class document_history:
			@staticmethod
			def insert(book: ACBFBook, index: int, entry: str):
				history_section = book.Metadata.document_info._info.find(f"{book._namespace}history")
				p = etree.Element(f"{book._namespace}p")
				history_section.insert(index, p)
				p.text = entry
				book.Metadata.document_info.sync_history()

			@staticmethod
			def append(book: ACBFBook, entry: str):
				idx = len(book.Metadata.document_info._info.findall(f"{book._namespace}history/{book._namespace}p"))
				metadata.documentinfo.document_history.insert(book, idx, entry)

			@staticmethod
			def edit(book: ACBFBook, index: int, text: str):
				item = book.Metadata.document_info._info.findall(f"{book._namespace}history/{book._namespace}p")[index]
				item.text = text
				book.Metadata.document_info.sync_history()

			@staticmethod
			def remove(book: ACBFBook, index: int):
				item = book.Metadata.document_info._info.findall(f"{book._namespace}history/{book._namespace}p")[index]
				item.clear()
				item.getparent().remove(item)
				book.Metadata.document_info.sync_history()
