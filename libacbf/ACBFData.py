from typing import Dict, List, Optional
from libacbf.BookData import BookData
from libacbf.Constants import BookNamespace

class ACBFData:
	"""
	docstring
	"""
	def __init__(self, root, ns: BookNamespace):
		self._ns = ns
		self._root = root
		self._base = root.find(f"{ns.ACBFns}data")
		self._data_elements = []

		self.files: Dict[str, Optional[BookData]] = {}

		self.update_data()

	def update_data(self):
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
		if self.files[key] is not None:
			return self.files[key]
		else:
			for i in self._data_elements:
				if i.attrib["id"] == key:
					new_data = BookData(key, i.attrib["content-type"], i.text)
					self.files[key] = new_data
					return new_data
