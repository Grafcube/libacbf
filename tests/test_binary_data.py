import json
from libacbf.ACBFBook import ACBFBook

sample_path = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book = ACBFBook(sample_path)

def test_data():
	op = {}
	for d in book.Data.keys():
		op[d] = {
			"type": book.Data[d].type,
			"data": book.Data[d].base64data
		}
	print(op)
	with open("tests/results/test_binary_data.json", "w", encoding="utf-8", newline="\n") as result:
		result.write(json.dumps(op, ensure_ascii=False))
