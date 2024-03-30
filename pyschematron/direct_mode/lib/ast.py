"""This module defines abstract base types for an Abstract Syntax Tree (AST) and an AST visitor."""
from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2024-03-21'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'LGPL v3'

from abc import abstractmethod, ABCMeta
from dataclasses import dataclass, fields
from typing import Any, Mapping, Iterable, Self


@dataclass(slots=True, frozen=True)
class GenericASTNode:
    """Abstract base class for Abstract Syntax Tree (AST) nodes.

    Each node in an AST (also the root) is of this type. Since we, in general, aim for immutability, the AST nodes
    are defined as frozen dataclasses with slots. If you want true immutability, avoid dictionaries and lists in
    your AST implementations.

    This class already implements the visitor pattern using the :class:`GenericASTVisitor`.
    """

    def accept_visitor(self, visitor: GenericASTVisitor) -> Any:
        """Accept a visitor on this node.

        Since Python allows polymorphic return values, we allow the visitor pattern to return values.

        Args:
            visitor: the visitor we accept and call

        Returns:
            The result of the visitor.
        """
        return visitor.visit(self)

    def get_init_values(self) -> dict[str, Any]:
        """Get the initialisation values with which this class was instantiated.

        Returns:
            A dictionary with the arguments which instantiated this object.
        """
        return {field.name: getattr(self, field.name) for field in fields(self)}

    def get_children(self) -> list[Self]:
        """Get a list of all the AST nodes in this node.

        This should return all the references to AST nodes in this node, all bundled in one list.

        Returns:
            All the child nodes in this node
        """
        def get_ast_nodes(init_values):
            children = []

            if isinstance(init_values, GenericASTNode):
                children.append(init_values)
            elif isinstance(init_values, Mapping):
                for el in init_values.values():
                    children.extend(get_ast_nodes(el))
            elif isinstance(init_values, Iterable) and not isinstance(init_values, str):
                for el in init_values:
                    children.extend(get_ast_nodes(el))

            return children

        return get_ast_nodes(self.get_init_values())


class GenericASTVisitor[T: GenericASTNode](metaclass=ABCMeta):
    """Generic base class for visitors, according to the visitor design pattern.

    Instead of a typed double dispatch we use dynamic double dispatching in which each node, when visited, calls
    the :meth:``visit` of this class instead of a visit method for each node type. This makes it easier to
    do edits on class names since the types can be looked up by an IDE.

    We use the generic type hint `T` to ensure solid type hinting for implementing visitors.
    """

    @abstractmethod
    def visit(self, ast_node: T) -> Any:
        """Visit the AST node.

        This uses dynamic dispatch to accept all types of AST nodes.

        Since Python allows polymorphic return values, we allow the visitor pattern to return values.

        Args:
            ast_node: an AST node of any type

        Returns:
            The result of the visitor.
        """

    def apply(self, ast_node: T) -> Any:
        """Convenience method to apply this visitor on the indicated node and get the result value.

        Args:
            ast_node: the node on which to apply this visitor

        Returns:
            The result value from :meth:`get_result`
        """
        return ast_node.accept_visitor(self)

