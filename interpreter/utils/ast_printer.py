from interpreter.expr import Visitor, Unary, Literal, Grouping, Binary, Expr
from interpreter.token import Token, TokenType


class AstPrinter(Visitor):
    def build(self, expr: Expr) -> str:
        return str(expr.accept(self))

    def visit_binary(self, expr: Binary) -> object:
        return self.parenthesize(expr.operator.lexeme, expr.left, expr.right)

    def visit_grouping(self, expr: Grouping) -> object:
        pass

    def visit_literal(self, expr: Literal) -> object:
        if expr.value is None:
            return 'nil'
        return str(expr.value)

    def visit_unary(self, expr: Unary) -> object:
        pass

    def parenthesize(self, name: str, *exprs) -> str:
        ret = '('
        ret += name
        for expr in exprs:
            ret += ' '
            ret += expr.accept(self)

        return ret + ')'


if __name__ == '__main__':
    expr = Binary(
        Literal(1),
        Token(TokenType.PLUS, '+', None, 1),
        Literal(2),
    )

    print(AstPrinter().build(expr))
