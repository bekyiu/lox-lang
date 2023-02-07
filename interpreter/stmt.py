# generate time: 2023-02-07 20:28:47
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
    def visit_block(self, stmt: Block) -> object:
        pass

    @abstractmethod
    def visit_expression(self, stmt: Expression) -> object:
        pass

    @abstractmethod
    def visit_if(self, stmt: If) -> object:
        pass

    @abstractmethod
    def visit_print(self, stmt: Print) -> object:
        pass

    @abstractmethod
    def visit_var(self, stmt: Var) -> object:
        pass


class Block(Stmt):
    statements: list[Stmt]

    def __init__(self, statements: list[Stmt], ):
        self.statements = statements

    def accept(self, visitor: StmtVisitor) -> object:
        return visitor.visit_block(self)


class Expression(Stmt):
    expression: Expr

    def __init__(self, expression: Expr, ):
        self.expression = expression

    def accept(self, visitor: StmtVisitor) -> object:
        return visitor.visit_expression(self)


class If(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Stmt

    def __init__(self, condition: Expr, then_branch: Stmt, else_branch: Stmt, ):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def accept(self, visitor: StmtVisitor) -> object:
        return visitor.visit_if(self)


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
