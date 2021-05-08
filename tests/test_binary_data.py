import json
from libacbf.ACBFBook import ACBFBook
from tests.testsettings import samples

sample_path = samples[0]
book = ACBFBook(sample_path)

def test_data():
	op = {}
	for i in book.Data.files.keys():
		op[i] = {
			"type": book.Data[i].type,
			"is_embedded": book.Data[i].is_embedded,
			"filesize": book.Data[i].filesize
		}
	print(op)
	with open("tests/results/test_binary_data.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(op, ensure_ascii=False))
	book.close()
