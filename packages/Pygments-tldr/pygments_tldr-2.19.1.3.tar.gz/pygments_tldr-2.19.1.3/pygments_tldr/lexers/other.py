"""
    pygments.lexers.other
    ~~~~~~~~~~~~~~~~~~~~~

    Just export lexer classes previously contained in this module.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

# ruff: noqa: F401
from pygments_tldr.lexers.sql import SqlLexer, MySqlLexer, SqliteConsoleLexer
from pygments_tldr.lexers.shell import BashLexer, BashSessionLexer, BatchLexer, \
    TcshLexer
from pygments_tldr.lexers.robotframework import RobotFrameworkLexer
from pygments_tldr.lexers.testing import GherkinLexer
from pygments_tldr.lexers.esoteric import BrainfuckLexer, BefungeLexer, RedcodeLexer
from pygments_tldr.lexers.prolog import LogtalkLexer
from pygments_tldr.lexers.snobol import SnobolLexer
from pygments_tldr.lexers.rebol import RebolLexer
from pygments_tldr.lexers.configs import KconfigLexer, Cfengine3Lexer
from pygments_tldr.lexers.modeling import ModelicaLexer
from pygments_tldr.lexers.scripting import AppleScriptLexer, MOOCodeLexer, \
    HybrisLexer
from pygments_tldr.lexers.graphics import PostScriptLexer, GnuplotLexer, \
    AsymptoteLexer, PovrayLexer
from pygments_tldr.lexers.business import ABAPLexer, OpenEdgeLexer, \
    GoodDataCLLexer, MaqlLexer
from pygments_tldr.lexers.automation import AutoItLexer, AutohotkeyLexer
from pygments_tldr.lexers.dsls import ProtoBufLexer, BroLexer, PuppetLexer, \
    MscgenLexer, VGLLexer
from pygments_tldr.lexers.basic import CbmBasicV2Lexer
from pygments_tldr.lexers.pawn import SourcePawnLexer, PawnLexer
from pygments_tldr.lexers.ecl import ECLLexer
from pygments_tldr.lexers.urbi import UrbiscriptLexer
from pygments_tldr.lexers.smalltalk import SmalltalkLexer, NewspeakLexer
from pygments_tldr.lexers.installers import NSISLexer, RPMSpecLexer
from pygments_tldr.lexers.textedit import AwkLexer
from pygments_tldr.lexers.smv import NuSMVLexer

__all__ = []
