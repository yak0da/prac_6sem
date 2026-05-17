"""Monster names and custom cow art."""

from io import StringIO

from cowsay import list_cows, read_dot_cow

JGSBAT_COW = r"""
$the_cow = <<EOC;
    ,_                    _,
    ) '-._  ,_    _,  _.-' (
    )  _.-'.|\\--//|.'-._  (
     )'   .'\/o\/o\/'.   `(
      ) .' . \====/ . '. (
       )  / <<    >> \  (
        '-._/``  ``\_.-'
  jgs     __\\'--'//__
         (((""`  `"")))
EOC
"""

_jgsbat = None


def get_jgsbat():
    """Return cowsay art for the jgsbat monster."""
    global _jgsbat
    if _jgsbat is None:
        _jgsbat = read_dot_cow(StringIO(JGSBAT_COW))
    return _jgsbat


KNOWN_MONSTERS = frozenset([*list_cows(), "jgsbat"])
