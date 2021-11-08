import pytest
from libacbf import ACBFBook
from libacbf.exceptions import InvalidBook


def test_no_acbf(results):
    with pytest.raises(InvalidBook):
        with ACBFBook(results / "fail.cbz") as _:
            pass


def test_references(results_book):
    with ACBFBook(results_book / "test_references.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Edit references"

        book.references["test_ref"] = {'_': "This is a new test reference."}
        book.references["electric_boogaloo"] = {'_': "This is another test reference.\nWith another line."}
        book.references["fancy"] = {
            '_': "This <strong>reference</strong> has <emphasis>fancy</emphasis> "
                 "<strikethrough>formatting</strikethrough>!\n"
                 "Here's <sub>some</sub> more <sup>formatting</sup>."
            }
        book._create_placeholders()


@pytest.mark.parametrize("ext, type", (("cbz", "Zip"), ("cb7", "SevenZip"), ("cbt", "Tar")))
def test_data(ext, type, results_data, samples):
    with ACBFBook(results_data / f"{type}.{ext}", 'w', type) as book:
        book.book_info.book_title['_'] = "Test Edit data"

        book.data.add_data(samples / "cover.jpg")
        book.book_info.coverpage.image_ref = "cover.jpg"

        book.data.add_data(samples / "page1.jpg")
        book.body.append_page("page1.jpg")

        book.data.add_data(samples / "page2.jpg", embed=True)
        book.body.append_page("#page2.jpg")

        book.data.add_data(samples / "page3.jpg", "003.jpg")
        book.body.append_page("003.jpg")

        book.data.add_data(samples / "page4.jpg", "REMOVE_ME.jpg")
        book.data.add_data(samples / "page4.jpg", "REMOVE_ME2.jpg", True)
        book.data.remove_data("REMOVE_ME.jpg")
        book.data.remove_data("REMOVE_ME2.jpg", embed=True)

        book._create_placeholders()


def test_styles(results_book, samples):
    with ACBFBook(results_book / "test_styles.cbz", 'w') as book:
        book.book_info.book_title['_'] = "Test Edit styles"

        book.styles.edit_style(samples / "test.css", '_')
        book.styles.edit_style(samples / "test.css", "embedded_test.css", embed=True)
        book.styles.edit_style(samples / "test.css", "REMOVE_ME.css", embed=True)
        book.styles.edit_style(samples / "test.css", "styles/REMOVE_ME.css")
        book.styles.edit_style(samples / "styles/test.scss", type="text/x-scss")
        book.styles.edit_style(samples / "styles/test.scss", "styles/style.scss", "text/x-scss")
        book.styles.remove_style("styles/REMOVE_ME.css")
        book.styles.remove_style("REMOVE_ME.css", embedded=True)

        book._create_placeholders()
