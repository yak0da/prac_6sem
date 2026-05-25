from pathlib import Path

import shutil

from doit.task import clean_targets

DOIT_CONFIG = {"default_tasks": ["html"]}

LOCALE = Path("mood/server/locale")
POT = LOCALE / "mud_msg.pot"
PO = LOCALE / "ru_RU.UTF-8/LC_MESSAGES/mud_msg.po"
MO = LOCALE / "ru_RU.UTF-8/LC_MESSAGES/mud_msg.mo"


def task_pot():
    """Extract strings into POT."""
    return {
        "file_dep": [Path("mood/server/localize.py")],
        "actions": [
            "python3 -m babel.messages.frontend extract "
            "-k gettext:2 -k ngettext:2,3 "
            f"-o {POT} mood/server/localize.py",
        ],
        "targets": [str(POT)],
        "clean": [clean_targets],
    }


def task_po():
    """Update PO from POT."""
    return {
        "file_dep": [str(POT)],
        "actions": [
            "python3 -m babel.messages.frontend update "
            f"-D mud_msg -i {POT} -d {LOCALE} -l ru_RU.UTF-8 --init-missing",
        ],
        "targets": [str(PO)],
        "task_dep": ["pot"],
        "clean": [clean_targets],
    }


def task_mo():
    """Compile MO from PO."""
    return {
        "file_dep": [str(PO)],
        "actions": [
            "python3 -m babel.messages.frontend compile "
            f"-D mud_msg -d {LOCALE} -l ru_RU.UTF-8",
        ],
        "targets": [str(MO)],
        "task_dep": ["po"],
        "clean": [clean_targets],
    }


def task_i18n():
    """Full translation build."""
    return {
        "actions": ["touch .i18n"],
        "targets": [".i18n"],
        "task_dep": ["pot", "po", "mo"],
        "clean": [clean_targets],
    }


def task_html():
    """Build HTML documentation."""
    rstpy = (
        list(Path("doc").glob("**/*.rst"))
        + list(Path("mood").glob("**/*.py"))
        + [Path("doc/conf.py")]
    )
    return {
        "actions": ["sphinx-build -M html doc doc/_build"],
        "targets": ["doc/_build/html/index.html"],
        "file_dep": rstpy,
        "clean": [(shutil.rmtree, ["doc/_build"], {"ignore_errors": True})],
    }


def _copy_docs_for_package():
    src = Path("doc/_build/html")
    dst = Path("mood/docs/html")
    if not (src / "index.html").is_file():
        raise FileNotFoundError(
            "Нет doc/_build/html — сначала: python3 -m doit html"
        )
    print(f"Копирование {src} -> {dst} ...")
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print("Готово.")


def task_docs_pkg():
    """Copy built HTML docs into the package tree."""
    return {
        "actions": [_copy_docs_for_package],
        "targets": ["mood/docs/html/index.html"],
        "task_dep": ["html"],
        "clean": [(shutil.rmtree, ["mood/docs/html"], {"ignore_errors": True})],
    }


def task_test():
    """Run client+server tests."""
    return {
        "file_dep": [str(MO), Path("test_commands.py")],
        "actions": ["python3 -m unittest test_commands", "touch .test"],
        "targets": [".test"],
        "task_dep": ["i18n"],
        "clean": [clean_targets],
    }
