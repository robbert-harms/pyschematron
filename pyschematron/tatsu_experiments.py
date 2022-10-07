__author__ = 'Robbert Harms'
__date__ = '2022-10-07'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


import tatsu
from tatsu.ast import AST

# from tatsu.model import ModelBuilderSemantics

grammar = r"""
@@grammar::CALC


start
    =
    expression $
    ;


expression
    =
    | left:expression op:'+' ~ right:term
    | left:expression op:'-' ~ right:term
    | term
    ;


term
    =
    | left:term op:'*' ~ right:factor
    | left:term '/' ~ right:factor
    | factor
    ;


factor
    =
    | '(' ~ @:expression ')'
    | number
    ;


number
    =
    /\d+/
    ;
"""

class Model:

    def __init__(self, number):
        self.number = number



class CalcBasicSemantics:
    def number(self, ast):
        return int(ast)

    def term(self, ast):
        if not isinstance(ast, AST):
            return Model(ast)
        elif ast.op == '*':
            return ast.left * ast.right
        elif ast.op == '/':
            return ast.left / ast.right
        else:
            raise Exception('Unknown operator', ast.op)

    def expression(self, ast):
        if not isinstance(ast, AST):
            return ast
        elif ast.op == '+':
            return ast.left + ast.right
        elif ast.op == '-':
            return ast.left - ast.right
        else:
            raise Exception('Unknown operator', ast.op)


parser = tatsu.compile(grammar)
ast = parser.parse('3 + 5 * ( 10 - 20 )', semantics=CalcBasicSemantics())

print(ast)

