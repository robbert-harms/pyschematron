__author__ = 'Robbert Harms'
__date__ = '2023-03-06'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'

from typing import Any, Mapping, Iterable, Literal, override

from abc import ABCMeta

from pyschematron.direct_mode.lib.ast import GenericASTVisitor
from pyschematron.direct_mode.schematron.ast import SchematronASTNode, Schema, ConcretePattern, Rule, ExtendsExternal, \
    ExternalRule, ConcreteRule, ExtendsById, AbstractRule, AbstractPattern, InstancePattern, Pattern, Phase
from pyschematron.direct_mode.schematron.utils import macro_expand


class SchematronASTVisitor(GenericASTVisitor[SchematronASTNode], metaclass=ABCMeta):
    """Visitor pattern for the Schematron AST nodes."""


class FindIdVisitor(SchematronASTVisitor):

    def __init__(self, id_ref: str):
        """A visitor which finds a node with the given ID.

        Args:
            id_ref: the id we would like to find in the visited nodes
        """
        super().__init__()
        self._id_ref = id_ref

    @override
    def visit(self, ast_node: SchematronASTNode) -> Any:
        if hasattr(ast_node, 'id') and getattr(ast_node, 'id') == self._id_ref:
            return ast_node

        for child in ast_node.get_children():
            if found_node := self.visit(child):
                return found_node


class GetIDMappingVisitor(SchematronASTVisitor):

    def __init__(self):
        """A visitor which maps all nodes with an id to their id."""
        super().__init__()
        self._result = {}

    @override
    def visit(self, ast_node: SchematronASTNode) -> Any:
        self._result |= self._visit(ast_node)
        return self._result

    def _visit(self, ast_node: SchematronASTNode) -> dict[str, SchematronASTNode]:
        for child in ast_node.get_children():
            child.accept_visitor(self)

        if hasattr(ast_node, 'id'):
            if (node_id := getattr(ast_node, 'id')) is not None:
                return {node_id: ast_node}
        return {}


class GetNodesOfTypeVisitor(SchematronASTVisitor):

    def __init__(self, types: type[SchematronASTNode] | tuple[type[SchematronASTNode], ...]):
        """A visitor which checks each node for their type against the type(s) provided

        Args:
            types: a single type or a tuple of types we check each node against.
        """
        super().__init__()
        self._types = types
        self._result = []

    @override
    def visit(self, ast_node: SchematronASTNode) -> Any:
        for child in ast_node.get_children():
            child.accept_visitor(self)

        if isinstance(ast_node, self._types):
            self._result.append(ast_node)

        return self._result


class ResolveExtendsVisitor(SchematronASTVisitor):

    def __init__(self, schema: Schema):
        """Simplify an AST Schema by inlining all the extends in the rules.

        This visitor inlines the variables and checks of each of the extended rules.
        `AbstractRule` and `ExternalRule` items are deleted after inlining.

        Args:
            schema: the full Schema as input to lookup all the rules by ID.
        """
        super().__init__()
        self._schema = schema

    @override
    def visit(self, ast_node: SchematronASTNode) -> SchematronASTNode:
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
        return schema.with_updated(patterns=tuple(patterns))

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
        return pattern.with_updated(rules=tuple(rules))

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

        checks = tuple(extra_checks) + rule.checks
        variables = tuple(extra_variables) + rule.variables
        return rule.with_updated(checks=checks, variables=variables, extends=tuple())

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


class ResolveAbstractPatternsVisitor(SchematronASTVisitor):

    def __init__(self, schema: Schema):
        """Simplify an AST Schema by expanding all the instance-of patterns.

        This visitor substitutes the abstract patterns with each of the instance-of patterns.
        All abstract patterns are deleted from the AST after replacement.

        Args:
            schema: the full Schema as input to lookup all the rules by ID.
        """
        super().__init__()
        self._schema = schema

    @override
    def visit(self, ast_node: SchematronASTNode) -> SchematronASTNode:
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

        return schema.with_updated(patterns=tuple(patterns))

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

        macro_expanded_pattern = macro_expand_visitor.apply(abstract_pattern)
        return macro_expanded_pattern.with_updated(id=instance_pattern.id)


class MacroExpandVisitor(SchematronASTVisitor):

    def __init__(self, macro_expansions: dict[str, str]):
        """Macro expand an abstract pattern.

        If the input is an AbstractPattern we return a ConcretePattern.
        In all other cases we return a node of the same type but with macro expanded elements.

        Args:
            A mapping of macro expansions to apply.
        """
        super().__init__()
        self._macro_expansions = macro_expansions

    @override
    def visit(self, ast_node: SchematronASTNode) -> SchematronASTNode:
        if isinstance(ast_node, AbstractPattern):
            expanded_pattern = self._visit_generic_node(ast_node)
            return ConcretePattern(**expanded_pattern.get_init_values())

        return self._visit_generic_node(ast_node)

    def _visit_generic_node[T: SchematronASTNode](self, ast_node: T) -> T:
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
                return tuple(_expand_value(el) for el in value)
            else:
                return value

        updated_items = {}
        for key, value in init_values.items():
            updated_items[key] = _expand_value(value)

        return ast_node.with_updated(**updated_items)


class PhaseSelectionVisitor(SchematronASTVisitor):

    def __init__(self, schema: Schema, phase: str | Literal['#ALL', '#DEFAULT'] | None = None):
        """Reduce an AST to only those patterns and phases referenced by a specific phase.

        This visitor only works on concrete Schema AST trees, we assume all abstract rules and patterns to be resolved.

        The output limits the `patterns` in the AST to only those selected by the phase.
        It will also limit the `phases` to the active phase, or to an empty list if no phase was specified.

        Args:
            schema: the full Schema as input to lookup all the rules by ID.
            phase: the phase we want to select, can be an IDREF of a phase node, the literal `#ALL` for all patterns,
                or `#DEFAULT` for the `defaultPhase` attribute of the Schematron. The default value is `#DEFAULT`,
                it is overwritten by the attribute `defaultPhase`, which again can be overwritten by the phase
                here specified.
        """
        super().__init__()
        self._schema = schema
        self._phase = phase
        self._phase_node = self._get_phase_node(schema, phase)

        self._active_pattern_ids = None
        if self._phase_node:
            self._active_pattern_ids = [active_phase.pattern_id for active_phase in self._phase_node.active]

    @override
    def visit(self, ast_node: SchematronASTNode) -> SchematronASTNode | bool:
        match ast_node:
            case Schema():
                return self._process_schema(ast_node)
            case Pattern():
                return self._process_pattern(ast_node)
            case Phase():
                return self._process_phase(ast_node)
            case _:
                return ast_node

    def _process_schema(self, schema: Schema) -> Schema:
        """Process a Schema by reducing the patterns and phases to the specified set.

        Args:
            schema: the schema to process

        Returns:
            A processed schema
        """
        patterns = tuple(pattern for pattern in schema.patterns if self.apply(pattern))
        phases = tuple(phase for phase in schema.phases if self.apply(phase))
        return schema.with_updated(patterns=patterns, phases=phases)

    def _process_pattern(self, pattern: Pattern) -> bool:
        """Process a pattern by verifying if it is in the current phase.

        Args:
            pattern: the pattern to process

        Returns:
            A boolean indicating if this pattern is in the current phase or not.
        """
        if not isinstance(pattern, ConcretePattern):
            raise ValueError('This visitor can only deal with concrete patterns.')

        return self._active_pattern_ids is None or pattern.id in self._active_pattern_ids

    def _process_phase(self, phase: Phase) -> bool:
        """Process a phase node by verifying if it is in the current phase.

        Args:
            phase: the phase to process

        Returns:
            A boolean indicating if this phase is in the current phase or not
        """
        return self._phase_node is None or phase.id == self._phase_node.id

    def _get_phase_node(self, schema: Schema, phase: str | Literal['#ALL', '#DEFAULT'] | None = None) -> Phase | None:
        """Get the phase node associated with the elected phase, or None if None found.

        Args:
            schema: the schema we want to search
            phase: the chosen phase.

        Returns:
            The AST phase node, or None if not applicable / not found.
        """
        if phase is None:
            phase = '#DEFAULT'

        if phase == '#ALL':
            return None

        if phase == '#DEFAULT':
            phase = schema.default_phase

        if isinstance(phase, str):
            phase_node = FindIdVisitor(phase).apply(self._schema)

            if phase_node is None:
                raise ValueError(f'Can not find the phase "{phase}".')
            return phase_node

        return None
