from io import BytesIO
from base64 import b64decode

class ACBFData:
	"""
	docstring
	"""
	def __init__(self, id: str, type: str, data: str):
		self.id: str = id
		self.type: str = type
		self.base64data: str = data

		self.data: BytesIO = BytesIO(b64decode(self.base64data, validate=True))
