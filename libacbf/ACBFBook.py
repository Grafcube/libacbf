from libacbf.ACBFBody import ACBFBody
from libacbf.ACBFMetadata import ACBFMetadata

class ACBFBook:
	"""
	docstring
	"""
	def __init__(self, file_path):
		"""
		docstring
		"""
		self.book_path = file_path

		self.metadata: ACBFMetadata = None # TBD

		self.body: ACBFBody = None # TBD
