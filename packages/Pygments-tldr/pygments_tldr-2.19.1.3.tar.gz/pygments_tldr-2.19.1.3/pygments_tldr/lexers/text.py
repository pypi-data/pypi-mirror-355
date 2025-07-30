"""
    pygments.lexers.text
    ~~~~~~~~~~~~~~~~~~~~

    Lexers for non-source code file types.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

# ruff: noqa: F401
from pygments_tldr.lexers.configs import ApacheConfLexer, NginxConfLexer, \
    SquidConfLexer, LighttpdConfLexer, IniLexer, RegeditLexer, PropertiesLexer, \
    UnixConfigLexer
from pygments_tldr.lexers.console import PyPyLogLexer
from pygments_tldr.lexers.textedit import VimLexer
from pygments_tldr.lexers.markup import BBCodeLexer, MoinWikiLexer, RstLexer, \
    TexLexer, GroffLexer
from pygments_tldr.lexers.installers import DebianControlLexer, DebianSourcesLexer, SourcesListLexer
from pygments_tldr.lexers.make import MakefileLexer, BaseMakefileLexer, CMakeLexer
from pygments_tldr.lexers.haxe import HxmlLexer
from pygments_tldr.lexers.sgf import SmartGameFormatLexer
from pygments_tldr.lexers.diff import DiffLexer, DarcsPatchLexer
from pygments_tldr.lexers.data import YamlLexer
from pygments_tldr.lexers.textfmts import IrcLogsLexer, GettextLexer, HttpLexer

__all__ = []
