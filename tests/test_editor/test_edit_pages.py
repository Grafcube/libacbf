import os
from pathlib import Path
from libacbf import ACBFBook

edit_dir = Path("tests/results/edit_body/")
os.makedirs(edit_dir, exist_ok=True)

def test_pages():
    with ACBFBook(edit_dir / "test_pages.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Pages")

        book.Body.pages[0].set_image_ref("page1.jpg")
        for n in range(1, 10):
            book.Body.insert_new_page(n, f"page{n + 1}.jpg")

        book.Body.insert_new_page(5, "pg6.png")
        book.Body.insert_new_page(3, "REMOVE ME.png")
        book.Body.insert_new_page(7, "SWAP 2.png")
        book.Body.insert_new_page(1, "SWAP 8.png")

        book.Body.remove_page(4)
        book.Body.change_page_index(7, 1)
        book.Body.change_page_index(2, 7)

def test_transition():
    with ACBFBook(edit_dir / "test_transition.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Page Transition")

        book.Body.pages[0].set_transition("none")
        book.Body.pages[0].set_transition(None)
        book.Body.pages[0].set_transition("scroll_down")

def test_title():
    with ACBFBook(edit_dir / "test_title.acbf", 'w', archive_type=None) as book:
        book.Metadata.book_info.edit_title("Test Page Title")

        book.Body.pages[0].set_title("A Page")
        book.Body.pages[0].set_title("Test Page", "en")
        book.Body.pages[0].set_title(None, "en")
        book.Body.pages[0].set_title("First Page", "en")
