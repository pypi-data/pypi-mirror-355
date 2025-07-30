"""
    pygments.lexers.math
    ~~~~~~~~~~~~~~~~~~~~

    Just export lexers that were contained in this module.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

# ruff: noqa: F401
from pygments_tldr.lexers.python import NumPyLexer
from pygments_tldr.lexers.matlab import MatlabLexer, MatlabSessionLexer, \
    OctaveLexer, ScilabLexer
from pygments_tldr.lexers.julia import JuliaLexer, JuliaConsoleLexer
from pygments_tldr.lexers.r import RConsoleLexer, SLexer, RdLexer
from pygments_tldr.lexers.modeling import BugsLexer, JagsLexer, StanLexer
from pygments_tldr.lexers.idl import IDLLexer
from pygments_tldr.lexers.algebra import MuPADLexer

__all__ = []
