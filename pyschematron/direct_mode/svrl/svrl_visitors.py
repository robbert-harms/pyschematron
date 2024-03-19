__author__ = 'Robbert Harms'
__date__ = '2024-03-17'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from abc import ABCMeta, abstractmethod
from typing import Any

from pyschematron.direct_mode.svrl.svrl_ast import SVRLNode


class SVRLASTVisitor(metaclass=ABCMeta):
    """Classes of this type represent visitors according to the visitor pattern.

    Instead of a typed double dispatch we use dynamic double dispatching in which each node, when visited, calls
    the :meth:``visit` of this class instead of a visit method for each node type. This makes it easier to
    do edits on class names since the types can be looked up by an IDE.
    """

    @abstractmethod
    def visit(self, svrl_node: SVRLNode) -> Any:
        """Visit the AST node.

        This uses dynamic dispatch to accept all types of SVRL AST nodes.

        Since Python allows polymorphic return values, we allow the visitor pattern to return values.

        Args:
            svrl_node: an AST node of any type

        Returns:
            The result of the visitor.
        """

    def apply(self, svrl_node: SVRLNode) -> Any:
        """Convenience method to apply this visitor on the indicated node and get the result value.

        Args:
            svrl_node: the node on which to apply this visitor

        Returns:
            The result value from :meth:`get_result`
        """
        return svrl_node.accept_visitor(self)
