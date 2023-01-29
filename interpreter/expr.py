# generate time: 2023-01-29 20:46:05
from abc import abstractmethod, ABCMeta

from interpreter.token import Token


# 所有表达式的抽象父类
class Expr(metaclass=ABCMeta):
    pass


class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr

    def __init__(self, left: Expr, operator: Token, right: Expr, ):
        self.left = left
        self.operator = operator
        self.right = right


class Grouping(Expr):
    expression: Expr

    def __init__(self, expression: Expr, ):
        self.expression = expression


class Literal(Expr):
    value: object

    def __init__(self, value: object, ):
        self.value = value


class Unary(Expr):
    operator: Token
    right: Expr

    def __init__(self, operator: Token, right: Expr, ):
        self.operator = operator
        self.right = right
