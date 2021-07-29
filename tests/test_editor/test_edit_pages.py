import os
from pathlib import Path
from libacbf import ACBFBook

edit_dir = Path("tests/results/edit_body/")
os.makedirs(edit_dir, exist_ok=True)


def test_pages():
    with ACBFBook(edit_dir / "test_pages.acbf", 'w', archive_type=None) as book:
        book.book_info.edit_title("Test Pages")

        book.body.pages[0].set_image_ref("page1.jpg")
        for n in range(1, 10):
            book.body.insert_new_page(n, f"page{n + 1}.jpg")

        book.body.insert_new_page(5, "pg6.png")
        book.body.insert_new_page(3, "REMOVE ME.png")
        book.body.insert_new_page(7, "SWAP 2.png")
        book.body.insert_new_page(1, "SWAP 8.png")

        book.body.remove_page(4)
        book.body.reorder_page(7, 1)
        book.body.reorder_page(2, 7)


def test_transition():
    with ACBFBook(edit_dir / "test_transition.acbf", 'w', archive_type=None) as book:
        book.book_info.edit_title("Test Page Transition")

        book.body.pages[0].set_transition("none")
        book.body.pages[0].set_transition(None)
        book.body.pages[0].set_transition("scroll_down")


def test_title():
    with ACBFBook(edit_dir / "test_title.acbf", 'w', archive_type=None) as book:
        book.book_info.edit_title("Test Page Title")

        book.body.pages[0].set_title("A Page")
        book.body.pages[0].set_title("Test Page", "en")
        book.body.pages[0].set_title(None, "en")
        book.body.pages[0].set_title("First Page", "en")
