import os
from pathlib import Path
from libacbf import ACBFBook

edit_dir = Path("tests/results/edit_book")
os.makedirs(edit_dir, exist_ok=True)


def test_references():
    with ACBFBook(edit_dir / "test_references.acbf", 'w', archive_type=None) as book:
        book.book_info.edit_title("Test Edit references")

        book.edit_reference("test_ref", "This is a new test reference.")
        book.edit_reference("electric_boogaloo", "This is another test reference.\nWith another line.")
        book.edit_reference("tb_deleted", "This one will be deleted.")
        book.edit_reference("test_ref", "This is an edited test reference.")
        book.remove_reference("tb_deleted")


def test_data():
    for ext, type in (("cbz", "Zip"), ("cb7", "SevenZip"), ("cbt", "Tar")):
        with ACBFBook(edit_dir / f"test_data.{ext}", 'w', type) as book:
            book.book_info.edit_title("Test Edit data")

            book.data.add_data("tests/samples/assets/cover.jpg")
            book.book_info.cover_page.set_image_ref("cover.jpg")

            book.data.add_data("tests/samples/assets/page1.jpg")
            book.body.pages[0].set_image_ref("page1")

            book.data.add_data("tests/samples/assets/page2.jpg", embed=True)
            book.body.insert_new_page(1, "#page2.jpg")

            book.data.add_data("tests/samples/assets/page3.jpg", "003.jpg")
            book.body.insert_new_page(2, "003.jpg")

            book.data.add_data("tests/samples/assets/page4.jpg", "to_be_removed.jpg")
            book.data.add_data("tests/samples/assets/page4.jpg", "to_be_removed2.jpg", True)
            book.data.remove_data("to_be_removed.jpg")
            book.data.remove_data("to_be_removed2.jpg", embed=True)


def test_styles():
    with ACBFBook(edit_dir / "test_styles.cbz", 'w') as book:
        book.book_info.edit_title("Test Edit styles")

        book.styles.edit_style("tests/samples/assets/styles/default.css", '_')
        book.styles.edit_style("tests/samples/assets/styles/styles.css", "styles/to_be_removed.css")
        book.styles.edit_style("tests/samples/assets/styles/sample.scss", type="text/x-scss")
        book.styles.edit_style("tests/samples/assets/styles/test.scss", "styles/style.scss", "text/x-scss")
        book.styles.remove_style("styles/to_be_removed.css")
