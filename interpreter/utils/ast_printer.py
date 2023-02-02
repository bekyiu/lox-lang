from interpreter.expr import Visitor, Unary, Literal, Grouping, Binary, Expr


class AstPrinter(Visitor):
    def build(self, expr: Expr) -> str:
        return str(expr.accept(self))

    def visit_binary(self, expr: Binary) -> object:
        return self.parenthesize(expr.operator.lexeme, expr.left, expr.right)

    def visit_grouping(self, expr: Grouping) -> object:
        return self.build(expr.expression)

    def visit_literal(self, expr: Literal) -> object:
        if expr.value is None:
            return 'nil'
        return str(expr.value)

    def visit_unary(self, expr: Unary) -> object:
        return self.parenthesize(expr.operator.lexeme, expr.right)

    def parenthesize(self, name: str, *exprs) -> str:
        ret = '('
        ret += name
        for expr in exprs:
            ret += ' '
            ret += expr.accept(self)

        return ret + ')'


if __name__ == '__main__':
    from interpreter.parser import Parser
    from interpreter.scanner import Scanner

    scanner = Scanner("((1 + 2) * (-3)) + 4 / 2")
    tokens = scanner.scan_tokens()
    print(tokens)
    parser = Parser(tokens)
    expr = parser.parse()

    print(AstPrinter().build(expr))
