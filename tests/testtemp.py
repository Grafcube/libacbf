import os
import shutil
from pprint import pprint
import tarfile as tar
from pathlib import Path
from tempfile import TemporaryDirectory
from libacbf import ACBFBook
from tests.testsettings import samples

# with ACBFBook(samples[1]) as book:
# 	for i in book.Body.pages:
# 		print(i.image_ref, len(i.image.data))

# with tar.open("tests/samples/more/test.tar.gz", 'w:gz') as arc:
# 	arc.add("tests/samples/more/cover.jpg", "cover.jpg")
# 	arc.add("tests/samples/more/JetBrainsMono[wght].ttf", "JetBrainsMono[wght].ttf")
# 	arc.list(False)

# Put this in save function
with TemporaryDirectory() as td:
	td = Path(td)
	with tar.open("tests/samples/more/test.tar.gz", 'r') as arc:
		arc.extractall(td)
	shutil.copy("tests/samples/more/cover.jpg", td/"copy.jpg")
	shutil.copy("tests/samples/more/JetBrainsMono[wght].ttf", td/"copy.ttf")
	os.makedirs(str(td/"more"), exist_ok=True)
	shutil.copy("tests/samples/more/JetBrainsMono[wght].ttf", td/"more/JetBrainsMono[wght].ttf")

	files = [x.relative_to(td) for x in td.rglob('*') if x.is_file()]

	with tar.open("tests/samples/more/test.tar.gz", 'w:gz') as arc:
		for i in files:
			arc.add(str(td/i), str(i))
		arc.list(False)
