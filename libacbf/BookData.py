from typing import Optional, Union
from io import BytesIO
from base64 import b64decode

class BookData:
	"""[summary]
	"""
	def __init__(self, id: str, file_type: str, data: Union[str, bytes, BytesIO]):
		self._base64data: Optional[str] = None

		self.id: str = id

		self.type: str = file_type

		dt = None
		if type(data) is str:
			self._base64data = data
			dt = BytesIO(b64decode(self._base64data))
		elif type(data) is BytesIO:
			dt = data
		elif type(data) is bytes:
			dt = BytesIO(data)

		self.is_embedded: bool = self._base64data is not None

		self.data: BytesIO = dt

	@property
	def filesize(self):
		"""[summary]

		Returns
		-------
		[type]
			[description]
		"""
		return self.data.getbuffer().nbytes
