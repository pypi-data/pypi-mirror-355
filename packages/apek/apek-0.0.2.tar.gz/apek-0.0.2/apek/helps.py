# -*- coding: utf-8 -*-
"""
Functions:
    language:
        Set the language for the help information. Currently supports en and zh.
    upgradeLog:
        Print the upgrade log with rich.
"""



from re import search as rematch
import rich as _rich  # noqa: F401
from rich.console import Console as _Console
from colorama import Fore, init as colorinit
from ._text import text
_console = _Console()
colorinit(autoreset=True)

_lang = "en"

def language(newlang="en"):
    """
    Set the language for the help information. Currently supports en and zh.
    
    Args:
        newlang (str, optional): The name of the language to be set. If no value is provided, it defaults to en.
    
    Returns:
        None
    
    Raises:
        ValueError: This error is raised when the provided language name is not supported.
    """
    
    global _lang
    if newlang not in text:
        raise ValueError(
            f"{text[_lang]['helps.function.setLang.languageNotSupport']}{Fore.GREEN}{repr(newlang)}{Fore.RESET}\n" +
            f"{text[_lang]['helps.function.setLang.languageNotSupport2']}{', '.join([i for i in list(text.keys()) if i not in ['default']])}"
        )
    _lang = newlang

def upgradeLog(v="0.0.2"):
    """
    Print the upgrade log with rich.
    
    Args:
        v (str, optional): Specify the version number for which to retrieve the log. The Defaults to the latest version.
    
    Returns:
        None
    
    Raises:
        ValueError: This error is raised when the provided version number does not conform to the "x.y.z" format.
    """
    
    v = v.strip()
    if not rematch("^\\d+\\.\\d+\\.\\d+$", v):
        raise ValueError(f"{text[_lang]['helps.function.updateLog.versionFormatError']}{Fore.GREEN}{repr(v)}{Fore.RESET}")
    nv = v.replace(".", "_")
    r = text[_lang].get("helps.upgradeLogs." + nv)
    if r is None:
        raise ValueError(f"{text[_lang]['helps.function.updateLog.versionNotFound']}{Fore.GREEN}{v}{Fore.RESET}")
    _console.print(r, highlight=False)
