from datetime import date

class ACBFBook:
	"""
	docstring
	"""
	def __init__():
		"""
		docstring
		"""
		pass

	class BookInfo:
		"""
		docstring
		"""
		def __init__(self, author, book_title, genre, annotation, cover_page, languages=None, text_layer=None,
					characters=None, keywords=None, sequence=None, content_rating=None, database_ref=None):
			"""
			docstring
			"""

			self.author = author
			self.book_title = book_title
			self.genre = genre
			self.annotation = annotation
			self.cover_page = cover_page
			self.languages = languages
			self.text_layer = text_layer
			self.characters = characters
			self.keywords = keywords
			self.sequence = sequence
			self.content_rating = content_rating
			self.database_ref = database_ref

	class PublishInfo:
		"""
		docstring
		"""
		def __init__(self, publisher: str, publish_date: date, publish_city: str =None, isbn: str =None,
					license: str =None):
			"""
			docstring
			"""
			self.publisher = publisher
			self.publish_date = publish_date
			self.publish_city = publish_city
			self.isbn = isbn
			self.license = license

	class DocumentInfo:
		"""
		docstring
		"""
		def __init__(self, author, creation_date: date, source=None, document_id: str =None,
					document_version: str =None, document_history=None):
			"""
			docstring
			"""
			self.author = author
			self.creation_date = creation_date
			self.source = source
			self.document_id = document_id
			self.document_version = document_version
			self.document_history = document_history
