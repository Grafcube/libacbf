import os
import json
import xmltodict

ctr = 0

def test_streaming(path, item):
	global ctr
	if ctr == 0:
		print(path[1][0])
		with open(f"tests/results/path{ctr}.json", "w", encoding="utf-8", newline="\n") as p:
			p.write(json.dumps(path))
		with open(f"tests/results/item{ctr}.json", "w", encoding="utf-8", newline="\n") as p:
			p.write(json.dumps(item))
		ctr += 1
		return True
	elif ctr == 1:
		print(path[1][0])
		with open(f"tests/results/path{ctr}.json", "w", encoding="utf-8", newline="\n") as p:
			p.write(json.dumps(path))
		with open(f"tests/results/item{ctr}.json", "w", encoding="utf-8", newline="\n") as p:
			p.write(json.dumps(item))
		ctr += 1
		return True
	elif ctr == 2:
		print(path[1][0])
		with open(f"tests/results/path{ctr}.json", "w", encoding="utf-8", newline="\n") as p:
			p.write(json.dumps(path))
		with open(f"tests/results/item{ctr}.json", "w", encoding="utf-8", newline="\n") as p:
			p.write(json.dumps(item))
		ctr += 1
		return True
	elif ctr == 3:
		print(path[1][0])
		with open(f"tests/results/path{ctr}.json", "w", encoding="utf-8", newline="\n") as p:
			p.write(json.dumps(path))
		with open(f"tests/results/item{ctr}.json", "w", encoding="utf-8", newline="\n") as p:
			p.write(json.dumps(item))
		ctr += 1
		return True
	elif ctr == 4:
		print(path[1][0])
		with open(f"tests/results/path{ctr}.json", "w", encoding="utf-8", newline="\n") as p:
			p.write(json.dumps(path))
		with open(f"tests/results/item{ctr}.json", "w", encoding="utf-8", newline="\n") as p:
			p.write(json.dumps(item))
		ctr += 1
		return False

with open("tests/samples/Doctorow, Cory - Craphound.acbf", encoding="utf-8") as book:
	if os.path.exists("demofile.txt"):
		os.remove("tests/samples/unparse.acbf")
	try:
		doc = xmltodict.parse(book.read(), item_depth=2, item_callback=test_streaming)
	except xmltodict.ParsingInterrupted:
		print("Parsing Interrupted")
	# new = xmltodict.unparse(doc, open("tests/samples/unparse.acbf", "w", encoding="utf-8"), pretty=True)
