from __future__ import annotations
import re
from typing import TYPE_CHECKING, List, Tuple
from collections import namedtuple
from functools import wraps
from lxml import etree

if TYPE_CHECKING:
    from libacbf import ACBFBook

from libacbf.constants import ArchiveTypes
from libacbf.exceptions import EditRARArchiveError

Vec2 = namedtuple("Vector2", "x y")


def check_book(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        check_write(self.book)
        func(self, *args, **kwargs)

    return wrapper


def check_write(book: ACBFBook):
    if book.mode == 'r':
        raise ValueError("Cannot edit read only book.")
    if not book.is_open:
        raise ValueError("Cannot edit closed book.")
    if book.archive is not None and book.archive.type == ArchiveTypes.Rar:
        raise EditRARArchiveError


def pts_to_vec(pts_str: str):
    pts = []
    pts_l = re.split(" ", pts_str)
    for pt in pts_l:
        ls = re.split(",", pt)
        pts.append(Vec2(int(ls[0]), int(ls[1])))
    return pts


def vec_to_pts(points: List[Tuple[int, int]]):
    return ' '.join([f"{x},{y}" for x, y in points])


def tree_to_para(p_root, ns):
    pa = []
    for p in p_root.findall(f"{ns}p"):
        p_text = str(etree.tostring(p, encoding="utf-8")).strip()
        text = re.sub(r'</?p[^>]*>', '', p_text)
        pa.append(text)
    return '\n'.join(pa)


def para_to_tree(paragraph: str, ns):
    p_elements = []
    for p in re.split(r'\n', paragraph):
        p = f"<p>{p}</p>"
        p_root = etree.fromstring(p)
        for i in p_root.iter():
            i.tag = ns + i.tag
        p_elements.append(p_root)
    return p_elements
