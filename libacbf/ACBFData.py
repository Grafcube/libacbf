from langcodes import Language

class Author:
	"""
	docstring
	"""
	def __init__(self, first_name: str, last_name: str, nickname: str =None, middle_name: str =None,
				homepage: str =None, email: str =None, activity: int =None,
				lang: Language =None):
		"""
		docstring
		"""
		self.first_name = first_name
		self.last_name = last_name
		self.nickname = nickname
		self.middle_name = middle_name
		self.homepage = homepage
		self.email = email
		self.activity = activity
		self.lang = lang
