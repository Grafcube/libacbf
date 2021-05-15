import pytest
from libacbf import ACBFBook
from tests.testsettings import samples

sample_path = samples[1]

book: ACBFBook = ACBFBook(sample_path)

@pytest.fixture(scope="session", autouse=True)
def run_around_tests():
	yield
	book.close()
