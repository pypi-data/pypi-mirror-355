"""
    pygments.lexers.agile
    ~~~~~~~~~~~~~~~~~~~~~

    Just export lexer classes previously contained in this module.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

# ruff: noqa: F401

from pygments_tldr.lexers.lisp import SchemeLexer
from pygments_tldr.lexers.jvm import IokeLexer, ClojureLexer
from pygments_tldr.lexers.python import PythonLexer, PythonConsoleLexer, \
    PythonTracebackLexer, Python3Lexer, Python3TracebackLexer, DgLexer
from pygments_tldr.lexers.ruby import RubyLexer, RubyConsoleLexer, FancyLexer
from pygments_tldr.lexers.perl import PerlLexer, Perl6Lexer
from pygments_tldr.lexers.d import CrocLexer, MiniDLexer
from pygments_tldr.lexers.iolang import IoLexer
from pygments_tldr.lexers.tcl import TclLexer
from pygments_tldr.lexers.factor import FactorLexer
from pygments_tldr.lexers.scripting import LuaLexer, MoonScriptLexer

__all__ = []
