"""Simple dictionary-based i18n helper."""

from __future__ import annotations

_lang: str = "ru"
_strings: dict[str, str] = {}


def set_language(lang: str) -> None:
    global _lang, _strings
    _lang = lang
    if lang == "en":
        from lazy_fit.i18n.en import strings
    else:
        from lazy_fit.i18n.ru import strings
    _strings = strings


def get_language() -> str:
    return _lang


def t(key: str) -> str:
    """Return translated string for *key*, falling back to the key itself."""
    return _strings.get(key, key)


# Initialise with default language
set_language("ru")
