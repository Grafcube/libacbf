import pytest
from libacbf import ACBFBook


def test_references(results_edit):
    with ACBFBook(results_edit / "test_references.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Edit references"

        book.references["test_ref"] = {'_': "This is a new test reference."}
        book.references["electric_boogaloo"] = {'_': "This is another test reference.\nWith another line."}
        book.references["fancy"] = {
            '_': "This <strong>reference</strong> has <emphasis>fancy</emphasis> "
                 "<strikethrough>formatting</strikethrough>!\n"
                 "Here's <sub>some</sub> more <sup>formatting</sup>."
            }
        book.create_placeholders()


@pytest.mark.parametrize("ext, type", (("cbz", "Zip"), ("cb7", "SevenZip"), ("cbt", "Tar")))
def test_data(ext, type, results_edit_data):
    with ACBFBook(results_edit_data / f"{type}.{ext}", 'w', type) as book:
        book.book_info.book_title['_'] = "Test Edit data"

        book.data.add_data("tests/samples/assets/cover.jpg")
        book.book_info.coverpage.image_ref = "cover.jpg"

        book.data.add_data("tests/samples/assets/page1.jpg")
        book.body.append_page("page1.jpg")

        book.data.add_data("tests/samples/assets/page2.jpg", embed=True)
        book.body.append_page("#page2.jpg")

        book.data.add_data("tests/samples/assets/page3.jpg", "003.jpg")
        book.body.append_page("003.jpg")

        book.data.add_data("tests/samples/assets/page4.jpg", "REMOVE_ME.jpg")
        book.data.add_data("tests/samples/assets/page4.jpg", "REMOVE_ME2.jpg", True)
        book.data.remove_data("REMOVE_ME.jpg")
        book.data.remove_data("REMOVE_ME2.jpg", embed=True)

        book.create_placeholders()


def test_styles(results_edit):
    with ACBFBook(results_edit / "test_styles.cbz", 'w') as book:
        book.book_info.book_title['_'] = "Test Edit styles"

        book.styles.edit_style("tests/samples/assets/test.css", '_')
        book.styles.edit_style("tests/samples/assets/test.css", "embedded_test.css", embed=True)
        book.styles.edit_style("tests/samples/assets/test.css", "REMOVE_ME.css", embed=True)
        book.styles.edit_style("tests/samples/assets/test.css", "styles/REMOVE_ME.css")
        book.styles.edit_style("tests/samples/assets/styles/test.scss", type="text/x-scss")
        book.styles.edit_style("tests/samples/assets/styles/test.scss", "styles/style.scss", "text/x-scss")
        book.styles.remove_style("styles/REMOVE_ME.css")
        book.styles.remove_style("REMOVE_ME.css", embedded=True)

        book.create_placeholders()
