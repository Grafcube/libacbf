from libacbf.ACBFBook import ACBFBook
from libacbf.Editor import BookManager

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book: ACBFBook = ACBFBook(sample)

# xml = f"<p>{p}</p>"

# root = etree.fromstring(bytes(xml, encoding="utf-8"))

# print("tag", root.tag)
# print("txt", root.text)
# print("tal", root.tail)

# for i in list(root):
# 	print("tag", i.tag)
# 	print("txt", i.text)
# 	print("tal", i.tail)

print(book.References)
p = "Text here lala. Oh... <strong>noice</strong>. Hey there. This is <emphasis>EPIC</emphasis>!\nOnce more! Another line! <strikethrough>Is this stupid</strikethrough>? <strong>NAH</strong>!"
BookManager.add_reference(book, "ref_003_test", p)
print(book.References)
