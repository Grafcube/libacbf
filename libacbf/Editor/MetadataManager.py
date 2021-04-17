from lxml import etree
from libacbf.Structs import Author
from libacbf.ACBFMetadata import ACBFMetadata

def add_book_author(metadata: ACBFMetadata, author: Author):
	ns = metadata._ns
	info_section = metadata.book_info._info

	au_element = etree.Element(f"{ns.ACBFns}author")

	if author.activity is not None:
		au_element.set("activity", author.activity.name)
	if author.lang is not None:
		au_element.set("lang", str(author.lang))

	if author.first_name is not None:
		element = etree.Element(f"{ns.ACBFns}first-name")
		element.text = author.first_name
		au_element.append(element)
	if author.last_name is not None:
		element = etree.Element(f"{ns.ACBFns}last-name")
		element.text = author.last_name
		au_element.append(element)
	if author.nickname is not None:
		element = etree.Element(f"{ns.ACBFns}nickname")
		element.text = author.nickname
		au_element.append(element)
	if author.middle_name is not None:
		element = etree.Element(f"{ns.ACBFns}middle-name")
		element.text = author.middle_name
		au_element.append(element)
	if author.home_page is not None:
		element = etree.Element(f"{ns.ACBFns}home-page")
		element.text = author.home_page
		au_element.append(element)
	if author.email is not None:
		element = etree.Element(f"{ns.ACBFns}email")
		element.text = author.email
		au_element.append(element)

	last_au_idx = 0
	if len(info_section.findall(f"{ns.ACBFns}author")) > 0:
		last_au_idx = info_section.index(info_section.findall(f"{ns.ACBFns}author")[-1])
	info_section.insert(last_au_idx+1, au_element)

	metadata.book_info.sync_authors()

def remove_book_author(metadata: ACBFMetadata, index: int):
	ns = metadata._ns
	info_section = metadata.book_info._info

	au_items = info_section.findall(f"{ns.ACBFns}author")
	au_items[index].clear()
	au_items[index].getparent().remove(au_items[index])

	metadata.book_info.sync_authors()
