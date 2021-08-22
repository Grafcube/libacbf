from libacbf import ACBFBook


def test_pages(results_edit_body):
    with ACBFBook(results_edit_body / "test_pages.acbf", 'w', archive_type=None) as book:
        book.book_info.book_title['_'] = "Test Pages"

        book.body.append_page("page1")
        book.body.append_page("page2")
        book.body.append_page("page4")
        book.body.append_page("REMOVE_ME")
        book.body.append_page("page5")
        book.body.insert_page(2, "page3")

        book.body.pages.pop(4)

        book.body.pages[0].set_transition("scroll_right")

        book.body.pages[0].title['_'] = "Test Page"
        book.body.pages[0].title["en"] = "First Page"
