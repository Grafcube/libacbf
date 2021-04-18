from typing import AnyStr
from re import split
from pathlib import Path
from base64 import b64encode
from magic import from_buffer
from lxml import etree
from libacbf.ACBFBook import ACBFBook, get_ACBF_data, get_references
from libacbf.ACBFMetadata import ACBFMetadata
from libacbf.Structs import Author
from libacbf.Constants import BookNamespace

class BookManager:
	"""
	docstring
	"""
	def __init__(self, book: ACBFBook):
		self.book = book

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

	def add_reference(self, id: AnyStr, paragraph: AnyStr, idx: int = -1):
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

	def remove_reference(self, id: AnyStr):
		ref_section = self._check_reference_section(False)
		if ref_section is not None:
			for i in ref_section.findall(f"{self.book.namespace.ACBFns}reference"):
				if i.attrib["id"] == id:
					i.clear()
					i.getparent().remove(i)
					break

			self.book.References = get_references(self.book.root.find(f"{self.book.namespace.ACBFns}references"), self.book.namespace)

	def add_data(self, file_path: AnyStr):
		dat_section = self._check_data_section()

		dat_path = Path(file_path)

		id = dat_path.name
		with open(file_path, 'rb') as file:
			content_type = from_buffer(file.read(2048), True)
			data64 = str(b64encode(file.read()), encoding="utf-8")

		bin_element = etree.Element(f"{self.book.namespace.ACBFns}binary")
		bin_element.set("id", id)
		bin_element.set("content-type", content_type)
		bin_element.text = data64

		dat_section.append(bin_element)
		self.book.Data = get_ACBF_data(self.book.root, self.book.namespace)

	def remove_data(self, id: AnyStr):
		dat_section = self._check_data_section(False)
		if dat_section is not None:
			for i in dat_section.findall(f"{self.book.namespace.ACBFns}binary"):
				if i.attrib["id"] == id:
					i.clear()
					i.getparent().remove(i)
					break

			self.book.Data = get_ACBF_data(self.book.root, self.book.namespace)

class MetadataManager:
	"""
	docstring
	"""
	def __init__(self, book: ACBFBook):
		self.metadata: ACBFMetadata = book.Metadata
		self.ns: BookNamespace = book.Metadata._ns

	def add_book_author(self, author: Author):
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

	def remove_book_author(self, index: int):
		info_section = self.metadata.book_info._info

		au_items = info_section.findall(f"{self.ns.ACBFns}author")
		au_items[index].clear()
		au_items[index].getparent().remove(au_items[index])

		self.metadata.book_info.sync_authors()
