from lxml import etree
from libacbf.BodyInfo import Page
from libacbf.ACBFBook import ACBFBook

sample = "tests/samples/Doctorow, Cory - Craphound-1.1.acbf"
book: ACBFBook = ACBFBook(sample)
txml = """<page>
<image href="https://upload.wikimedia.org/wikipedia/commons/a/a9/ComicsPortal.png"/>
</page>
"""
p = etree.fromstring(txml)
for i in list(iter(p)):
	i.tag = book.namespace.ACBFns + i.tag

pg = Page(p, book)
print(pg.image.id)
print(pg.image.is_embedded)
print(pg.image.type)
print(pg.image.data.getbuffer().nbytes)
