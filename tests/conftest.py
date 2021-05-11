import pytest
from libacbf.ACBFBook import ACBFBook

samples = ["tests/samples/Doctorow, Cory - Craphound-1.0.acbf",
		"tests/samples/Doctorow, Cory - Craphound.cbz",
		"tests/samples/Doctorow, Cory - Craphound.cb7",
		"tests/samples/Doctorow, Cory - Craphound - Copy.cbz", # Should always fail because it does not contain ACBF XML file.
		"tests/samples/Doctorow, Cory - Craphound.gz.cbt",
		"tests/samples/Doctorow, Cory - Craphound.cbr"
		]

sample_path = samples[1]

book: ACBFBook = ACBFBook(sample_path)

@pytest.fixture(scope="session", autouse=True)
def run_around_tests():
	yield
	book.close()
