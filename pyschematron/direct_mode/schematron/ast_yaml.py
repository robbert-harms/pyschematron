from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2023-02-21'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'

import dataclasses
import inspect
from abc import ABCMeta, abstractmethod
from io import StringIO
from pathlib import PosixPath, Path
from typing import Callable, Any, Mapping, Iterable

from ruyaml import YAML, BaseRepresenter, BaseConstructor, Node

import pyschematron.direct_mode.schematron.ast
from pyschematron.direct_mode.schematron.ast import SchematronASTNode


class ASTYamlConverter(metaclass=ABCMeta):

    @abstractmethod
    def load(self, stream: Path | Any) -> SchematronASTNode:
        """Load a provided stream into a Schematron AST node.

        Args:
            stream: the stream with Yaml data to load, either a path to a file, or some sort of (binary) string.

        Returns:
            The loaded Schematron AST node.
        """

    @abstractmethod
    def dump(self, data: SchematronASTNode, stream: Path | Any | None = None) -> str | None:
        """Dump the provided data into YAML format.

        Args:
            data: the Schematron AST node to dump
            stream: the stream to dump the data to, either a file path, or some sort of string buffer.
                This is optional, if not provided we return a string.

        Returns:
            If no stream was provided, we return the output as a string. Else we dump the output to the provided stream.
        """


class RuyamlASTYamlConverter(ASTYamlConverter):

    def __init__(self):
        """Basic AST to YAML (and back) converter.

        This works together with the ruyaml library to dump and load AST nodes to and from yaml.
        """
        self._codec = _ASTYamlCodec()

    def load(self, stream: Path | Any) -> SchematronASTNode:
        return self._codec.load(stream)

    def dump(self, data: SchematronASTNode, stream: Path | Any | None = None) -> str | None:
        if stream is None:
            with StringIO() as dumped:
                self._codec.dump(data, dumped)
                return dumped.getvalue()
        else:
            self._codec.dump(data, stream)


class _ASTYamlCodec(YAML):

    def __init__(self, *args, **kwargs):
        """Specialized RuYAML loader and dumper for :class:`SchematronASTNode` instances.

        For loading the YAML, the ruyaml library uses shared mutable lists to construct the class hierarchy.
        Since we are creating immutable AST nodes, we need a builder pattern to construct the final classes.
        During processing of the YAML, the :class:`YamlRepresenter` create :class:`SchematronASTNodeBuilder` nodes.
        As a final step, the build method of these builders is called to construct the final AST nodes.
        """
        super().__init__(*args, typ='safe', **kwargs)
        self._add_ast_representers()

    def load(self, stream: Path | Any) -> Any:
        loaded_objects = super().load(stream)
        if isinstance(loaded_objects, SchematronASTNodeBuilder):
            return loaded_objects.build()
        return loaded_objects

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

    def _list_representable_ast_nodes(self) -> list[type[SchematronASTNode]]:
        """List the representable AST nodes.

        Returns:
            Get a list of AST nodes we can YAML represent.
        """
        def filter_function(el):
            return inspect.isclass(el) and issubclass(el, SchematronASTNode) and el is not SchematronASTNode
        return [el[1] for el in inspect.getmembers(pyschematron.direct_mode.schematron.ast, filter_function)]

    def _get_representer(self, ast_node: type[SchematronASTNode]) -> "YamlRepresenter":
        """Get a representor for the indicated node type.

        Args:
            ast_node: the type of AST node for which we want a representer.

        Returns:
            A representer for this specific node type.
        """
        return GenericASTNodeYamlRepresenter(ast_node)


class YamlRepresenter(metaclass=ABCMeta):
    """Specialized class for YAML representing elements and contents of :class:`SchematronASTNode`.

    This works in conjunction with the Ruyaml library.
    """

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
            A function to create the yaml representation.
        """

    @abstractmethod
    def get_loading_function(self) -> Callable[[BaseConstructor, Node], Any]:
        """Get the loading function we can use to load the YAML node into a `SchematronASTNode`.

        Returns:
            A function to load the yaml representation.
        """


class PathRepresenter(YamlRepresenter):

    @property
    def element_class(self) -> Any:
        return PosixPath

    @property
    def yaml_tag(self) -> str:
        return f'!Path'

    def get_dumping_function(self) -> Callable[[BaseRepresenter, Any], Node]:
        def to_yaml(representer: BaseRepresenter, node: Any) -> Node:
            return representer.represent_scalar(self.yaml_tag, str(node))
        return to_yaml

    def get_loading_function(self) -> Callable[[BaseConstructor, Node], Any]:
        def from_yaml(constructor: BaseConstructor, node: Node) -> Any:
            return self.element_class(node.value)
        return from_yaml


class ASTNodeYamlRepresenter(YamlRepresenter):

    def get_dumping_function(self) -> Callable[[BaseRepresenter, Any], Node]:
        def to_yaml(representer: BaseRepresenter, node: SchematronASTNode) -> Node:
            return self._to_yaml(representer, node)
        return to_yaml

    def get_loading_function(self) -> Callable[[BaseConstructor, Node], Any]:
        def from_yaml(constructor: BaseConstructor, node: Node) -> SchematronASTNodeBuilder:
            return self._from_yaml(constructor, node)
        return from_yaml

    @abstractmethod
    def _to_yaml(self, representer: BaseRepresenter, node: SchematronASTNode) -> Node:
        """The YAML dumping function.

        This is the actual function used to dump a specific Schematron node to YAML.

        Returns:
            The ruyaml Node used to dump to YAML.
        """

    @abstractmethod
    def _from_yaml(self, constructor: BaseConstructor, node: Node) -> SchematronASTNodeBuilder:
        """The function to load a ruyaml YAML Node into a Schematron AST Node.

        Returns:
            A builder for the Schematron node.
        """


class GenericASTNodeYamlRepresenter(ASTNodeYamlRepresenter):

    def __init__(self, node_type: type[SchematronASTNode]):
        """Create a basic representer for :class:`SchematronASTNode`.

        When loading a YAML, this class returns :class:`SchematronASTNodeBuilder` nodes.

        Args:
            node_type: the type of node we are representing
        """
        self._node_type = node_type

    @property
    def element_class(self) -> type[SchematronASTNode]:
        return self._node_type

    @property
    def yaml_tag(self) -> str:
        return f'!{self._node_type.__name__}'

    def _to_yaml(self, representer: BaseRepresenter, node: SchematronASTNode) -> Node:
        """Internal function called by the forwarding function in `get_dumping_function`"""
        init_names = [f.name for f in dataclasses.fields(self.element_class) if f.init]

        node_data = {}
        for init_name in init_names:
            if value := getattr(node, init_name):
                node_data[init_name] = value

        return representer.represent_mapping(self.yaml_tag, node_data)

    def _from_yaml(self, constructor: BaseConstructor, node: Node) -> SchematronASTNodeBuilder:
        """Internal function called by the forwarding function in `get_loading_function`"""
        values = constructor.construct_mapping(node)
        return DictionaryNodeBuilder(self._node_type, values)


class SchematronASTNodeBuilder(metaclass=ABCMeta):
    """Builder pattern for delayed construction of Schematron nodes."""

    @abstractmethod
    def build(self) -> SchematronASTNode:
        """Build a Schematron node based on the information in this builder.

        Returns:
            The constructed schematron element.
        """


class DictionaryNodeBuilder(SchematronASTNodeBuilder):

    def __init__(self, node_type: type[SchematronASTNode], init_values: dict):
        """Construct a Schematron AST node using a dictionary containing the init values.

        During the build phase, this builder will transform the provided init values according to these rules:
        1. if a node contains a builder, build it
        2. if a node contains a list, modify it to become a tuple

        Args:
            node_type: the type of node we will build
            init_values: the init values to pass to the constructor.
        """
        self._node_type = node_type
        self._init_values = init_values

    def build(self) -> SchematronASTNode:
        def _expand_value(value):
            if isinstance(value, SchematronASTNodeBuilder):
                return value.build()
            elif isinstance(value, str):
                return value
            elif isinstance(value, Mapping):
                return {k: _expand_value(v) for k, v in value.items()}
            elif isinstance(value, Iterable):
                return tuple(_expand_value(el) for el in value)
            else:
                return value

        final_inits = {}
        for key, value in self._init_values.items():
            final_inits[key] = _expand_value(value)

        return self._node_type(**final_inits)
