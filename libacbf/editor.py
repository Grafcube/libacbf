from __future__ import annotations

import re
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
