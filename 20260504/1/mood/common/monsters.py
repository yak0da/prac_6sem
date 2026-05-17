"""Monster names and custom cow art."""

from importlib import resources

from cowsay import list_cows, read_dot_cow

_jgsbat = None


def get_jgsbat():
    """Return cowsay art for the jgsbat monster."""
    global _jgsbat
    if _jgsbat is None:
        cow_path = resources.files("mood.common") / "jgsbat.cow"
        with cow_path.open(encoding="utf-8") as cow_file:
            _jgsbat = read_dot_cow(cow_file)
    return _jgsbat


KNOWN_MONSTERS = frozenset([*list_cows(), "jgsbat"])
