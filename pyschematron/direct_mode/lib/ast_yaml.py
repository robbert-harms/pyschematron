__author__ = 'Robbert Harms'
__date__ = '2023-02-21'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

import dataclasses
import inspect
import sys
from abc import ABCMeta, abstractmethod
from pathlib import PosixPath
from typing import Callable, Any, Type

from ruyaml import YAML, BaseRepresenter, BaseConstructor, Node

import pyschematron.direct_mode.ast
from pyschematron.direct_mode.ast import SchematronASTNode


class ASTYaml(YAML):

    def __init__(self, *args, **kwargs):
        """Specialized YAML loader and dumper for :class:`SchematronASTNode` instances."""
        super().__init__(*args, typ='safe', **kwargs)
        self._add_ast_representers()

    def _add_ast_representers(self):
        """Add YAML representers (loading and dumping) for all relevant types in `pyschematron.ast`.

        This modifies the current instance by adding representer objects.
        """
        representers = self._get_ast_node_representers()
        representers.append(PathRepresenter())

        for representer in representers:
            self.representer.add_representer(representer.element_class, representer.get_dumping_function())
            self.constructor.add_constructor(representer.yaml_tag, representer.get_loading_function())

    def _get_ast_node_representers(self) -> list["YamlRepresenter"]:
        """Get representers for all the :class:`SchematronASTNode` nodes.

        Returns:
            A list of YAML representers for the AST nodes.
        """
        ast_nodes = self._list_representable_ast_nodes()
        return [self._get_representer(ast_node) for ast_node in ast_nodes]

    def _list_representable_ast_nodes(self) -> list[Type[SchematronASTNode]]:
        """List the representable AST nodes.

        Returns:
            Get a list of AST nodes we can YAML represent.
        """
        def filter_function(el):
            return inspect.isclass(el) and issubclass(el, SchematronASTNode) and el is not SchematronASTNode
        return [el[1] for el in inspect.getmembers(pyschematron.direct_mode.ast, filter_function)]

    def _get_representer(self, ast_node: Type[SchematronASTNode]) -> "YamlRepresenter":
        """Get a representor for the indicated node type.

        Args:
            ast_node: the type of AST node for which we want a representer.

        Returns:
            A representer for this specific node type.
        """
        return ASTNodeYamlRepresenter(ast_node)


class YamlRepresenter(metaclass=ABCMeta):
    """Specialized class for YAML representing elements and contents of :class:`SchematronASTNode`."""

    @property
    @abstractmethod
    def element_class(self) -> Any:
        """Get the type of element this representer represents."""

    @property
    @abstractmethod
    def yaml_tag(self) -> str:
        """Get the YAML tag for the class representation."""

    @abstractmethod
    def get_dumping_function(self) -> Callable[[BaseRepresenter, Any], Callable]:
        """Get the dumping function `to_yaml` we can use to dump the item to YAML.

        Returns:
            A function to create the yaml representation. This is usually a function `to_yaml` attached to the
            class instance.
        """

    @abstractmethod
    def get_loading_function(self) -> Callable[[BaseConstructor, Node], Any]:
        """Get the loading function we can use to load the YAML node into a `SchematronASTNode`.

        Returns:
            A function to load the yaml representation. This is usually a function `to_yaml` attached to the
            class instance.
        """


class PathRepresenter(YamlRepresenter):

    @property
    def element_class(self) -> Any:
        return PosixPath

    @property
    def yaml_tag(self) -> str:
        return f'!Path'

    def get_dumping_function(self) -> Callable[[BaseRepresenter, Any], Callable]:
        def to_yaml(representer: BaseRepresenter, node: Any) -> Callable:
            return representer.represent_scalar(self.yaml_tag, str(node))
        return to_yaml

    def get_loading_function(self) -> Callable[[BaseConstructor, Node], Any]:
        def from_yaml(constructor: BaseConstructor, node: Node) -> Any:
            return self.element_class(node.value)
        return from_yaml


class ASTNodeYamlRepresenter(YamlRepresenter):

    def __init__(self, node_type: Type[SchematronASTNode]):
        """Create a basic representer for :class:`SchematronASTNode`.

        Args:
            node: the type of node we are representing
        """
        self._node_type = node_type

    @property
    def element_class(self) -> Type[SchematronASTNode]:
        return self._node_type

    @property
    def yaml_tag(self) -> str:
        return f'!{self._node_type.__name__}'

    def get_dumping_function(self) -> Callable[[BaseRepresenter, Any], Callable]:
        def to_yaml(representer: BaseRepresenter, node: SchematronASTNode) -> Callable:
            return self._to_yaml(representer, node)
        return to_yaml

    def get_loading_function(self) -> Callable[[BaseConstructor, Node], Any]:
        def from_yaml(constructor: BaseConstructor, node: Node) -> Any:
            return self._from_yaml(constructor, node)
        return from_yaml

    def _to_yaml(self, representer: BaseRepresenter, node: SchematronASTNode) -> Callable:
        """Internal function called by the forwarding function in `get_dumping_function`"""
        init_names = [f.name for f in dataclasses.fields(self.element_class) if f.init]

        node_data = {}
        for init_name in init_names:
            if value := getattr(node, init_name):
                node_data[init_name] = value

        return representer.represent_mapping(self.yaml_tag, node_data)

    def _from_yaml(self, constructor: BaseConstructor, node: Node) -> Any:
        """Internal function called by the forwarding function in `get_loading_function`"""
        values = constructor.construct_mapping(node)
        return self.element_class(**values)
