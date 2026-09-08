"""Pick the copy module for a language. Both mirror the same names."""
from __future__ import annotations

from . import strings_am, strings_en


def strings(lang: str | None):
    return strings_en if lang == "en" else strings_am
