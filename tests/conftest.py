import pytest
from libacbf import ACBFBook
from tests.testres import samples

@pytest.fixture(scope="module")
def read_books():
	books = {x: ACBFBook(x, 'r') for x in samples.values()}
	yield books
	for i in books.values():
		i.close()

@pytest.fixture(scope="module")
def edit_books():
	books = {x: ACBFBook(x, 'a') for x in samples.values()}
	yield books
	for i in books.values():
		i.close()

def get_au_op(i):
	new_op = i.__dict__.copy()
	new_op.pop("_element")
	new_op["activity"] = new_op["_activity"].name if new_op["_activity"] is not None else None
	new_op.pop("_activity")
	new_op["lang"] = new_op["_lang"]
	new_op.pop("_lang")
	new_op["first_name"] = new_op["_first_name"]
	new_op.pop("_first_name")
	new_op["last_name"] = new_op["_last_name"]
	new_op.pop("_last_name")
	return new_op
