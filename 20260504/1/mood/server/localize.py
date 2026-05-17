"""Server-side message localization."""

from pathlib import Path

from babel.support import NullTranslations, Translations

_LOCALE_DIR = Path(__file__).resolve().parent / "locale"
_CACHE = {}


def get_translations(locale):
    """Load and cache Babel translations for ``locale``."""
    if not locale:
        return NullTranslations()
    if locale not in _CACHE:
        loaded = Translations.load(
            str(_LOCALE_DIR),
            locales=[locale],
            domain="mud_msg",
        )
        _CACHE[locale] = loaded if loaded else NullTranslations()
    return _CACHE[locale]


def gettext(locale, message, **params):
    """Translate ``message`` for ``locale``."""
    text = get_translations(locale).gettext(message)
    if params:
        return text % params
    return text


def ngettext(locale, singular, plural, n):
    """Translate plural form for ``locale``."""
    return get_translations(locale).ngettext(singular, plural, n)


def hp_text(locale, count):
    """Format hit points with correct plural form."""
    text = ngettext(locale, "%(n)d hp", "%(n)d hp", count)
    return text % {"n": count}


def render_event(locale, event):
    """Build a localized line from an event tuple."""
    kind, data = event
    if kind == "locale_set":
        return gettext(
            locale,
            "Set up locale: %(name)s",
            name=data["name"],
        )
    if kind == "joined":
        return gettext(
            locale,
            "%(username)s joined MUD",
            username=data["username"],
        )
    if kind == "left":
        return gettext(
            locale,
            "%(username)s left MUD",
            username=data["username"],
        )
    if kind == "placed":
        hp = hp_text(locale, data["hp"])
        return gettext(
            locale,
            "%(username)s placed monster %(name)s with %(hp)s at (%(x)s, %(y)s)",
            username=data["username"],
            name=data["name"],
            hp=hp,
            x=data["x"],
            y=data["y"],
        )
    if kind == "attack":
        damage = hp_text(locale, data["damage"])
        left = hp_text(locale, data["left"])
        msg = gettext(
            locale,
            "%(username)s attacked %(monster)s with %(weapon)s, "
            "damage %(damage)s, %(monster)s has %(left)s",
            username=data["username"],
            monster=data["monster"],
            weapon=data["weapon"],
            damage=damage,
            left=left,
        )
        if data.get("killed"):
            msg += gettext(
                locale,
                ", %(monster)s was killed",
                monster=data["monster"],
            )
        return msg
    return str(event)
