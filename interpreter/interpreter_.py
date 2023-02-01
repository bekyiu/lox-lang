from interpreter.expr import Visitor, Expr, Binary, Grouping, Literal, Unary
from interpreter.parser import Parser
from interpreter.scanner import Scanner
from interpreter.token import TokenType
from interpreter.utils.ast_printer import AstPrinter


class Interpreter(Visitor):
    def evaluate(self, expr: Expr) -> object:
        return expr.accept(self)

    def visit_binary(self, expr: Binary) -> object:
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)

        op_type = expr.operator.type
        if op_type == TokenType.BANG_EQUAL:
            return not self._is_equal(left, right)
        if op_type == TokenType.EQUAL_EQUAL:
            return self._is_equal(left, right)
        if op_type == TokenType.GREATER:
            return float(left) > float(right)
        if op_type == TokenType.GREATER_EQUAL:
            return float(left) >= float(right)
        if op_type == TokenType.LESS:
            return float(left) < float(right)
        if op_type == TokenType.LESS_EQUAL:
            return float(left) <= float(right)

        if op_type == TokenType.PLUS:
            if isinstance(left, float) and isinstance(right, float):
                return float(left) + float(right)
            if isinstance(left, str) and isinstance(right, str):
                return str(left) + str(right)

        if op_type == TokenType.MINUS:
            return float(left) - float(right)
        if op_type == TokenType.STAR:
            return float(left) * float(right)
        if op_type == TokenType.SLASH:
            return float(left) / float(right)

        raise RuntimeError('visit_unary')

    def visit_grouping(self, expr: Grouping) -> object:
        return self.evaluate(expr.expression)

    def visit_literal(self, expr: Literal) -> object:
        return expr.value

    def visit_unary(self, expr: Unary) -> object:
        right = self.evaluate(expr.right)

        op_type = expr.operator.type
        if op_type == TokenType.MINUS:
            return -float(right)
        if op_type == TokenType.BANG:
            return self._is_true(right)

        raise RuntimeError('visit_unary')

    def _is_true(self, val: object) -> bool:
        return False if val is None else isinstance(val, bool)

    def _is_equal(self, a: object, b: object) -> bool:
        if a is None and b is None:
            return True
        if a is None:
            return False
        return a == b


if __name__ == '__main__':
    scanner = Scanner("((1 + 2) * (-3)) + 4 / 2")
    tokens = scanner.scan_tokens()
    print(tokens)
    parser = Parser(tokens)
    expr = parser.parse()

    print(AstPrinter().build(expr))
    print(Interpreter().evaluate(expr))
