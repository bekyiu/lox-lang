# generate time: 2023-02-02 21:22:43
from __future__ import annotations

from abc import abstractmethod, ABCMeta

from interpreter.expr import Expr


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
