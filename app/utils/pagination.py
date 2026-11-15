"""Pagination helper that works with SQLAlchemy Query objects.

The returned object supports both attribute access (used by Jinja templates,
mirroring Flask-SQLAlchemy's Pagination) and item access (used by the JSON
API serializers).
"""
from __future__ import annotations

from math import ceil


class Pagination:
    """A tiny, framework-independent pagination result."""

    __slots__ = (
        "items",
        "total",
        "page",
        "pages",
        "per_page",
        "has_prev",
        "has_next",
        "prev_num",
        "next_num",
    )

    def __init__(self, items, total: int, page: int, per_page: int):
        pages = max(1, ceil(total / per_page)) if total else 1
        self.items = items
        self.total = total
        self.page = min(page, pages)
        self.pages = pages
        self.per_page = per_page
        self.has_prev = self.page > 1
        self.has_next = self.page < pages
        self.prev_num = self.page - 1
        self.next_num = self.page + 1

    def __getitem__(self, key: str):
        if key in self.__slots__:
            return getattr(self, key)
        raise KeyError(key)

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def keys(self):
        return self.__slots__


def paginate(query, page: int = 1, per_page: int = 9) -> Pagination:
    page = max(1, int(page or 1))
    per_page = max(1, min(int(per_page or 9), 100))
    total = query.order_by(None).count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return Pagination(items, total, page, per_page)
