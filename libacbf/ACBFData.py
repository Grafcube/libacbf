from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Optional
if TYPE_CHECKING:
	from libacbf.ACBFBook import ACBFBook

from libacbf.BookData import BookData

class ACBFData:
	"""
	docstring
	"""
	def __init__(self, book: ACBFBook):
		self._ns = book.namespace
		self._root = book.root
		self._base = book.root.find(f"{self._ns.ACBFns}data")
		self._data_elements = []

		self.files: Dict[str, Optional[BookData]] = {}

		self.sync_data()

	def sync_data(self):
		self._base = self._root.find(f"{self._ns.ACBFns}data")
		if self._base is not None:
			self._data_elements = self._base.findall(f"{self._ns.ACBFns}binary")
		for i in self._data_elements:
			self.files[i.attrib["id"]] = None

	def list_files(self) -> List[str]:
		fl = []
		for i in self.files.keys():
			fl.append(str(i))
		return fl

	def __len__(self):
		return len(self.files.keys())

	def __getitem__(self, key: str):
		if key in self.files.keys():
			if self.files[key] is not None:
				return self.files[key]
			else:
				for i in self._data_elements:
					if i.attrib["id"] == key:
						new_data = BookData(key, i.attrib["content-type"], i.text)
						self.files[key] = new_data
						return new_data
		else:
			raise FileNotFoundError
