# generate time: 2023-02-11 12:28:22
from __future__ import annotations
from abc import abstractmethod, ABCMeta

from interpreter.expr import Expr
from interpreter.token_ import Token


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
    def visit_function(self, stmt: Function) -> object:
        pass

    @abstractmethod
    def visit_break(self, stmt: Break) -> object:
        pass

    @abstractmethod
    def visit_continue(self, stmt: Continue) -> object:
        pass

    @abstractmethod
    def visit_if(self, stmt: If) -> object:
        pass

    @abstractmethod
    def visit_print(self, stmt: Print) -> object:
        pass

    @abstractmethod
    def visit_while(self, stmt: While) -> object:
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


class Function(Stmt):
    name: Token
    params: list[Token]
    body: list[Stmt]

    def __init__(self, name: Token, params: list[Token], body: list[Stmt], ):
        self.name = name
        self.params = params
        self.body = body

    def accept(self, visitor: StmtVisitor) -> object:
        return visitor.visit_function(self)


class Break(Stmt):
    break_: Token

    def __init__(self, break_: Token, ):
        self.break_ = break_

    def accept(self, visitor: StmtVisitor) -> object:
        return visitor.visit_break(self)


class Continue(Stmt):
    continue_: Token

    def __init__(self, continue_: Token, ):
        self.continue_ = continue_

    def accept(self, visitor: StmtVisitor) -> object:
        return visitor.visit_continue(self)


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


class While(Stmt):
    condition: Expr
    body: Stmt

    def __init__(self, condition: Expr, body: Stmt, ):
        self.condition = condition
        self.body = body

    def accept(self, visitor: StmtVisitor) -> object:
        return visitor.visit_while(self)


class Var(Stmt):
    name: Token
    initializer: Expr

    def __init__(self, name: Token, initializer: Expr, ):
        self.name = name
        self.initializer = initializer

    def accept(self, visitor: StmtVisitor) -> object:
        return visitor.visit_var(self)
