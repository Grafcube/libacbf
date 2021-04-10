from typing import AnyStr
from re import split
from pathlib import Path
from lxml import etree
from magic import from_buffer
from base64 import b64encode
from libacbf.ACBFBook import ACBFBook, get_ACBF_data, get_references

def _check_reference_section(book: ACBFBook):
	ref_section = book.root.find(f"{book.namespace.ACBFns}references")
	if ref_section is None:
		idx = book.root.index(book.root.find(f"{book.namespace.ACBFns}body"))
		ref_section = etree.Element(f"{book.namespace.ACBFns}references")
		book.root.insert(idx+1, ref_section)
	return ref_section

def _check_data_section(book: ACBFBook):
	dat_section = book.root.find(f"{book.namespace.ACBFns}data")
	if dat_section is None:
		ref_section = book.root.find(f"{book.namespace.ACBFns}references")
		if ref_section is None:
			idx = book.root.index(book.root.find(f"{book.namespace.ACBFns}body"))
		else:
			idx = book.root.index(ref_section)
		dat_section = etree.Element(f"{book.namespace.ACBFns}data")
		book.root.insert(idx+1, dat_section)
	return dat_section

def add_reference(book: ACBFBook, id: AnyStr, paragraph: AnyStr, idx: int = -1):
	ref_section = _check_reference_section(book)

	ref_element = etree.Element(f"{book.namespace.ACBFns}reference")
	ref_element.set("id", id)

	p_list = split(r"\n", paragraph)
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

	book.References = get_references(book.root.find(f"{book.namespace.ACBFns}references"), book.namespace)

def add_data(book: ACBFBook, file_path: AnyStr):
	dat_section = _check_data_section(book)

	dat_path = Path(file_path)

	id = dat_path.name
	with open(file_path, 'rb') as file:
		content_type = from_buffer(file.read(2048), True)
		data64 = str(b64encode(file.read()), encoding="utf-8")

	bin_element = etree.Element(f"{book.namespace.ACBFns}binary")
	bin_element.set("id", id)
	bin_element.set("content-type", content_type)
	bin_element.text = data64

	dat_section.append(bin_element)
	book.Data = get_ACBF_data(book.root, book.namespace)
