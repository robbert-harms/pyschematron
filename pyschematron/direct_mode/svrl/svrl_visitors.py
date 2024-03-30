__author__ = 'Robbert Harms'
__date__ = '2024-03-17'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from abc import ABCMeta

from pyschematron.direct_mode.lib.ast import GenericASTVisitor
from pyschematron.direct_mode.svrl.ast import SVRLNode


class SVRLASTVisitor(GenericASTVisitor[SVRLNode], metaclass=ABCMeta):
    """Visitor implementation for the SVRL nodes."""
    ...
