"""
    pygments.lexers.compiled
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Just export lexer classes previously contained in this module.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

# ruff: noqa: F401
from pygments_tldr.lexers.jvm import JavaLexer, ScalaLexer
from pygments_tldr.lexers.c_cpp import CLexer, CppLexer
from pygments_tldr.lexers.d import DLexer
from pygments_tldr.lexers.objective import ObjectiveCLexer, \
    ObjectiveCppLexer, LogosLexer
from pygments_tldr.lexers.go import GoLexer
from pygments_tldr.lexers.rust import RustLexer
from pygments_tldr.lexers.c_like import ECLexer, ValaLexer, CudaLexer
from pygments_tldr.lexers.pascal import DelphiLexer, PortugolLexer, Modula2Lexer
from pygments_tldr.lexers.ada import AdaLexer
from pygments_tldr.lexers.business import CobolLexer, CobolFreeformatLexer
from pygments_tldr.lexers.fortran import FortranLexer
from pygments_tldr.lexers.prolog import PrologLexer
from pygments_tldr.lexers.python import CythonLexer
from pygments_tldr.lexers.graphics import GLShaderLexer
from pygments_tldr.lexers.ml import OcamlLexer
from pygments_tldr.lexers.basic import BlitzBasicLexer, BlitzMaxLexer, MonkeyLexer
from pygments_tldr.lexers.dylan import DylanLexer, DylanLidLexer, DylanConsoleLexer
from pygments_tldr.lexers.ooc import OocLexer
from pygments_tldr.lexers.felix import FelixLexer
from pygments_tldr.lexers.nimrod import NimrodLexer
from pygments_tldr.lexers.crystal import CrystalLexer

__all__ = []
