__author__ = 'Robbert Harms'
__date__ = '2023-03-06'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@altoida.com'

from typing import Any, Mapping, Iterable

from abc import ABCMeta, abstractmethod

from pyschematron.direct_mode.ast import SchematronASTNode, Schema, ConcretePattern, Rule, ExtendsExternal, \
    ExternalRule, ConcreteRule, ExtendsById, AbstractRule, AbstractPattern, InstancePattern
from pyschematron.direct_mode.lib.utils import macro_expand


class ASTVisitor(metaclass=ABCMeta):
    """Classes of this type represent visitors according to the visitor pattern.

    Instead of a typed double dispatch we use dynamic double dispatching in which each node, when visited calls
    the :meth:``visit` of this class instead of a visit method for each node type. This makes it easier to
    do edits on class names since the types can be looked up by an IDE.
    """

    @abstractmethod
    def visit(self, ast_node: SchematronASTNode) -> None:
        """Visit the AST node.

        This uses dynamic dispatch to accept all types of Schematron AST nodes.

        Args:
            ast_node: an AST node of any type
        """


class ASTVisitorWithResult(ASTVisitor, metaclass=ABCMeta):
    __slots__ = ['_result']

    def __init__(self):
        """A specialized AST visitor which support return values.

        The typical use of this visitor is with recursion on which a new visitor object of the same type
        is created for every new return value.
        """
        self._result = None

    def visit(self, ast_node: SchematronASTNode) -> None:
        self._result = self._visit(ast_node)

    def apply(self, ast_node: SchematronASTNode) -> Any:
        """Convenience method to apply this visitor on the indicated node and get the result value.

        Args:
            ast_node: the node on which to apply this visitor

        Returns:
            The result value from :meth:`get_result`
        """
        ast_node.accept_visitor(self)
        return self.get_result()

    def get_result(self) -> Any:
        """Get the result of applying this visitor.

        Returns:
            Generic return value, typically an AST node or a list of AST nodes.
        """
        return self._result

    @abstractmethod
    def _visit(self, ast_node: SchematronASTNode) -> Any:
        """Visit the indicated node and return a return value.

        Args:
            ast_node: the node to visit

        Returns:
            Any value you wish to return. Note that this visitor may be called multiple times for
                different nodes.
        """


class FindIdVisitor(ASTVisitorWithResult):
    __slots__ = ['_id_ref']

    def __init__(self, id_ref: str):
        """A visitor which finds a node with the given ID.

        Args:
            id_ref: the id we would like to find in the visited nodes
        """
        super().__init__()
        self._id_ref = id_ref

    def _visit(self, ast_node: SchematronASTNode) -> SchematronASTNode | None:
        if hasattr(ast_node, 'id') and getattr(ast_node, 'id') == self._id_ref:
            return ast_node

        for child in ast_node.get_children():
            if found_node := FindIdVisitor(self._id_ref).apply(child):
                return found_node


class GetIDMapping(ASTVisitorWithResult):
    __slots__ = ['_id_mapping']

    def __init__(self):
        """A visitor which maps all nodes with an id to their id"""
        super().__init__()
        self._result = {}

    def visit(self, ast_node: SchematronASTNode) -> None:
        self._result.update(self._visit(ast_node))

    def _visit(self, ast_node: SchematronASTNode) -> dict[str, SchematronASTNode]:
        for child in ast_node.get_children():
            child.accept_visitor(self)

        if hasattr(ast_node, 'id'):
            if (node_id := getattr(ast_node, 'id')) is not None:
                return {node_id: ast_node}
        return {}


class ResolveExtendsVisitor(ASTVisitorWithResult):
    __slots__ = ['_schema']

    def __init__(self, schema: Schema):
        """Simplify an AST Schema by inlining all the extends in the rules.

        This visitor inlines the variables and checks of each of the extended rules.
        `AbstractRule` and `ExternalRule` items are deleted after inlining.

        Args:
            schema: the full Schema as input to lookup all the rules by ID.
        """
        super().__init__()
        self._schema = schema

    def _visit(self, ast_node: SchematronASTNode) -> SchematronASTNode:
        match ast_node:
            case Schema():
                return self._process_schema(ast_node)
            case ConcretePattern() | AbstractPattern():
                return self._process_pattern(ast_node)
            case Rule():
                return self._process_rule(ast_node)
            case ExtendsExternal():
                return self._process_extends_external(ast_node)
            case ExtendsById():
                return self._process_extends_by_id(ast_node)
            case _:
                return ast_node

    def _process_schema(self, schema: Schema) -> Schema:
        """Process a Schema by processing all the patterns.

        Args:
            schema: the schema to process

        Returns:
            A processed schema
        """
        patterns = []
        for pattern in schema.patterns:
            patterns.append(ResolveExtendsVisitor(self._schema).apply(pattern))
        return schema.with_updated(patterns=patterns)

    def _process_pattern(self, pattern: ConcretePattern | AbstractPattern) -> ConcretePattern | AbstractPattern:
        """Process a pattern by processing all the rules.

        Args:
            pattern: the pattern to process

        Returns:
            the processed pattern
        """
        rules = []
        for rule in pattern.rules:
            processed_rule = ResolveExtendsVisitor(self._schema).apply(rule)
            if isinstance(processed_rule, ConcreteRule):
                rules.append(processed_rule)
        return pattern.with_updated(rules=rules)

    def _process_rule(self, rule: Rule) -> Rule:
        """Process a rule by inlining all the extends.

        Args:
            rule: the rule we wish to process

        Returns:
            A new rule with all the extends loaded and added to the checks.
        """
        extra_checks = []
        extra_variables = []
        for extends in rule.extends:
            extended_rule = ResolveExtendsVisitor(self._schema).apply(extends)
            extra_checks.extend(extended_rule.checks)
            extra_variables.extend(extended_rule.variables)

        checks = extra_checks + rule.checks
        variables = extra_variables + rule.variables
        return rule.with_updated(checks=checks, variables=variables, extends=[])

    def _process_extends_by_id(self, extends: ExtendsById) -> AbstractRule:
        """Process an extends which points to an abstract rule.

        Args:
            extends: the extends node we are processing

        Returns:
            The abstract rule this extends points to.
        """
        abstract_rule = FindIdVisitor(extends.id_ref).apply(self._schema)
        if abstract_rule is None:
            raise ValueError(f'Can\'t find the abstract rule with id "{extends.id_ref}"')
        return ResolveExtendsVisitor(self._schema).apply(abstract_rule)

    def _process_extends_external(self, extends: ExtendsExternal) -> ExternalRule:
        """Process an external extend by returning the loaded rule.

        Args:
            extends: the extends node we are processing

        Returns:
            The loaded external rule
        """
        return ResolveExtendsVisitor(self._schema).apply(extends.rule)


class ResolveAbstractPatternsVisitor(ASTVisitorWithResult):
    __slots__ = ['_schema']

    def __init__(self, schema: Schema):
        """Simplify an AST Schema by expanding all the instance-of patterns.

        This visitor substitutes the abstract patterns with each of the instance-of patterns.
        All abstract patterns are deleted from the AST after replacement.

        Args:
            schema: the full Schema as input to lookup all the rules by ID.
        """
        super().__init__()
        self._schema = schema

    def _visit(self, ast_node: SchematronASTNode) -> SchematronASTNode:
        match ast_node:
            case Schema():
                return self._process_schema(ast_node)
            case InstancePattern():
                return self._process_instance_pattern(ast_node)
            case _:
                return ast_node

    def _process_schema(self, schema: Schema) -> Schema:
        """Process a Schema by processing all the patterns.

        Args:
            schema: the schema to process

        Returns:
            A processed schema
        """
        patterns = []
        for pattern in schema.patterns:
            new_pattern = ResolveAbstractPatternsVisitor(self._schema).apply(pattern)
            if isinstance(new_pattern, ConcretePattern):
                patterns.append(new_pattern)

        return schema.with_updated(patterns=patterns)

    def _process_instance_pattern(self, instance_pattern: InstancePattern) -> ConcretePattern:
        """Process an instance-of pattern by expanding it with an abstract pattern.

        Args:
            instance_pattern: the instance-of pattern to process

        Returns:
            the processed pattern as a concrete pattern
        """
        abstract_pattern = FindIdVisitor(instance_pattern.abstract_id_ref).apply(self._schema)
        if abstract_pattern is None:
            raise ValueError(f'Can\'t find the abstract pattern with id "{instance_pattern.abstract_id_ref}"')

        macro_expansions = {f'${param.name}': param.value for param in instance_pattern.params}
        macro_expand_visitor = MacroExpandVisitor(macro_expansions)

        return macro_expand_visitor.apply(abstract_pattern)


class MacroExpandVisitor(ASTVisitorWithResult):
    __slots__ = ['_macro_expansions']

    def __init__(self, macro_expansions: dict[str, str]):
        """Macro expand an abstract pattern.

        If the input is an AbstractPattern we return a ConcretePattern.
        In all other cases we return a node of the same type but with macro expanded elements.

        Args:
            A mapping of macro expansions to apply.
        """
        super().__init__()
        self._macro_expansions = macro_expansions

    def _visit(self, ast_node: SchematronASTNode) -> SchematronASTNode:
        if isinstance(ast_node, AbstractPattern):
            expanded_pattern = self._visit_generic_node(ast_node)
            return ConcretePattern(**expanded_pattern.get_init_values())

        return self._visit_generic_node(ast_node)

    def _visit_generic_node(self, ast_node: SchematronASTNode) -> SchematronASTNode:
        """Visit a generic node and do macro expansion.

        Args:
            ast_node: the node we are visiting and expanding

        Returns:
            A node of the same type but with macro expanded items.
        """
        sub_visitor = MacroExpandVisitor(self._macro_expansions)
        init_values = ast_node.get_init_values()

        def _expand_value(value):
            if isinstance(value, str):
                return macro_expand(value, self._macro_expansions)
            elif isinstance(value, SchematronASTNode):
                return sub_visitor.apply(value)
            elif isinstance(value, Mapping):
                return {k: _expand_value(v) for k, v in value.items()}
            elif isinstance(value, Iterable):
                return [_expand_value(el) for el in value]
            else:
                return value

        updated_items = {}
        for key, value in init_values.items():
            updated_items[key] = _expand_value(value)

        return ast_node.with_updated(**updated_items)
