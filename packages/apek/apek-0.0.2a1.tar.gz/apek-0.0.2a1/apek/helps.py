# -*- coding: utf-8 -*-

from re import search as rematch
import rich as _rich
from rich.console import Console as _Console
from colorama import Fore, init as colorinit
from ._text import text
_console = _Console()
colorinit(autoreset=True)

_lang = "en"

def language(newlang="en"):
    global _lang
    if newlang not in text:
        raise ValueError(f"{text[_lang]['helps.function.setLang.languageNotSupport']}{Fore.GREEN}{repr(newlang)}{Fore.RESET}")
    _lang = newlang

def upgradeLog(v="0.0.2"):
    v = v.strip()
    if not rematch("^\\d+\\.\\d+\\.\\d+$", v):
        raise ValueError(f"{text[_lang]['helps.function.updateLog.versionFormatError']}{Fore.GREEN}{repr(v)}{Fore.RESET}")
    nv = v.replace(".", "_")
    r = text[_lang].get("helps.upgradeLogs." + nv)
    if r is None:
        raise ValueError(f"{text[_lang]['helps.function.updateLog.versionNotFound']}{Fore.GREEN}{v}{Fore.RESET}")
    _console.print(r, highlight=False)
