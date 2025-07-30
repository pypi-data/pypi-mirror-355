"""
    pygments.lexers.web
    ~~~~~~~~~~~~~~~~~~~

    Just export previously exported lexers.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

# ruff: noqa: F401
from pygments_tldr.lexers.html import HtmlLexer, DtdLexer, XmlLexer, XsltLexer, \
    HamlLexer, ScamlLexer, JadeLexer
from pygments_tldr.lexers.css import CssLexer, SassLexer, ScssLexer
from pygments_tldr.lexers.javascript import JavascriptLexer, LiveScriptLexer, \
    DartLexer, TypeScriptLexer, LassoLexer, ObjectiveJLexer, CoffeeScriptLexer
from pygments_tldr.lexers.actionscript import ActionScriptLexer, \
    ActionScript3Lexer, MxmlLexer
from pygments_tldr.lexers.php import PhpLexer
from pygments_tldr.lexers.webmisc import DuelLexer, XQueryLexer, SlimLexer, QmlLexer
from pygments_tldr.lexers.data import JsonLexer
JSONLexer = JsonLexer  # for backwards compatibility with Pygments 1.5

__all__ = []
