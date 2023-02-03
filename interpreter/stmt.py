# generate time: 2023-02-03 20:53:17
from __future__ import annotations

from abc import abstractmethod, ABCMeta

from interpreter.expr import Expr
from interpreter.token import Token


class Stmt(metaclass=ABCMeta):
    @abstractmethod
    def accept(self, visitor: StmtVisitor) -> object:
        pass


class StmtVisitor(metaclass=ABCMeta):

    @abstractmethod
    def visit_expression(self, stmt: Expression) -> object:
        pass

    @abstractmethod
    def visit_print(self, stmt: Print) -> object:
        pass

    @abstractmethod
    def visit_var(self, stmt: Var) -> object:
        pass


class Expression(Stmt):
    expression: Expr

    def __init__(self, expression: Expr, ):
        self.expression = expression

    def accept(self, visitor: StmtVisitor) -> object:
        return visitor.visit_expression(self)


class Print(Stmt):
    expression: Expr

    def __init__(self, expression: Expr, ):
        self.expression = expression

    def accept(self, visitor: StmtVisitor) -> object:
        return visitor.visit_print(self)


class Var(Stmt):
    name: Token
    initializer: Expr

    def __init__(self, name: Token, initializer: Expr, ):
        self.name = name
        self.initializer = initializer

    def accept(self, visitor: StmtVisitor) -> object:
        return visitor.visit_var(self)
