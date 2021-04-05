from typing import AnyStr
from re import split
from lxml import etree
from libacbf.ACBFBook import ACBFBook, get_references

def _check_reference_section(book: ACBFBook):
	ref_section = book.root.find(f"{book.Namespace.ACBFns}references")
	if type(ref_section) is None:
		idx = book.root.index(book.root.find(f"{book.Namespace.ACBFns}body"))
		ref_section = etree.Element(f"{book.Namespace.ACBFns}references")
		book.root.insert(idx+1, ref_section)
	return ref_section

def add_reference(book: ACBFBook, id: AnyStr, paragraph: AnyStr, idx: int = -1):
	ref_section = _check_reference_section(book)

	ref_element = etree.Element(f"{book.Namespace.ACBFns}reference")
	ref_element.set("id", id)

	p_list = split(r"\n", paragraph)
	for ref in p_list:
		p = f"<p>{ref}</p>"
		p_element = etree.fromstring(bytes(p, encoding="utf-8"))
		for i in list(p_element.iter()):
			i.tag = book.Namespace.ACBFns + i.tag
		ref_element.append(p_element)

	if idx == -1:
		ref_section.append(ref_element)
	elif idx < 0:
		ref_section.insert(idx+1, ref_element)
	else:
		ref_section.insert(idx, ref_element)

	book.References = get_references(book.root.find(f"{book.Namespace.ACBFns}references"), book.Namespace)
