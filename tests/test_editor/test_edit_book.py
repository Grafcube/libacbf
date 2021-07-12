from libacbf import ACBFBook

def test_references(edit_dir):
    with ACBFBook(edit_dir/"test_references.acbf", 'w', archive_type=None) as book:
        book.edit_reference("test_ref", "This is a new test reference.")
        book.edit_reference("electric_boogaloo",
                            "This is another test reference.\nWith another line.")
        book.edit_reference("tb_deleted", "This one will be deleted.")
        book.edit_reference("test_ref", "This is an edited test reference.")
        book.remove_reference("tb_deleted")

def test_data(edit_dir):
    with ACBFBook(edit_dir / "test_data.cbz", 'w') as book:
        book.Data.add_data("tests/samples/assets/cover.jpg")
        book.Metadata.book_info.cover_page.set_image_ref("cover.jpg")

        book.Data.add_data("tests/samples/assets/page1.jpg")
        book.Body.pages[0].set_image_ref("page1")

        book.Data.add_data("tests/samples/assets/page2.jpg", embed=True)
        book.Body.insert_new_page(1, "#page2.jpg")

        book.Data.add_data("tests/samples/assets/page3.jpg", "003.jpg")
        book.Body.insert_new_page(2, "003.jpg")

        book.Data.add_data("tests/samples/assets/page4.jpg", "to_be_removed.jpg")
        book.Data.add_data("tests/samples/assets/page4.jpg", "to_be_removed2.jpg", True)
        book.Data.remove_data("to_be_removed.jpg")
        book.Data.remove_data("to_be_removed2.jpg", embedded=True)

def test_styles(edit_dir):
    with ACBFBook(edit_dir / "test_styles.cbz", 'w') as book:
        book.Styles.edit_style("tests/samples/assets/styles/default.css", embed=True)
        book.Styles.edit_style("tests/samples/assets/styles/styles.css",
                               "styles/to_be_removed.css")
        book.Styles.edit_style("tests/samples/assets/styles/sample.scss", type="text/x-scss")
        book.Styles.edit_style("tests/samples/assets/styles/test.scss",
                               "styles/style.scss",
                               "text/x-scss")
        book.Styles.remove_style("styles/to_be_removed.css")
