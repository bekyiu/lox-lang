# generate time: 2023-01-30 20:34:48
from __future__ import annotations
from abc import abstractmethod, ABCMeta
from interpreter.token import Token


class Expr(metaclass=ABCMeta):
    @abstractmethod
    def accept(self, visitor: ExprVisitor) -> object:
        pass


class ExprVisitor(metaclass=ABCMeta):

    @abstractmethod
    def visit_binary(self, expr: Binary) -> object:
        pass

    @abstractmethod
    def visit_grouping(self, expr: Grouping) -> object:
        pass

    @abstractmethod
    def visit_literal(self, expr: Literal) -> object:
        pass

    @abstractmethod
    def visit_unary(self, expr: Unary) -> object:
        pass


class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr

    def __init__(self, left: Expr, operator: Token, right: Expr, ):
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: ExprVisitor) -> object:
        return visitor.visit_binary(self)


class Grouping(Expr):
    expression: Expr

    def __init__(self, expression: Expr, ):
        self.expression = expression

    def accept(self, visitor: ExprVisitor) -> object:
        return visitor.visit_grouping(self)


class Literal(Expr):
    value: object

    def __init__(self, value: object, ):
        self.value = value

    def accept(self, visitor: ExprVisitor) -> object:
        return visitor.visit_literal(self)


class Unary(Expr):
    operator: Token
    right: Expr

    def __init__(self, operator: Token, right: Expr, ):
        self.operator = operator
        self.right = right

    def accept(self, visitor: ExprVisitor) -> object:
        return visitor.visit_unary(self)
