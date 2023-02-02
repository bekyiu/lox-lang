from interpreter.error import RuntimeException
from interpreter.expr import Visitor, Expr, Binary, Grouping, Literal, Unary
from interpreter.lox import Lox
from interpreter.parser import Parser
from interpreter.scanner import Scanner
from interpreter.token import TokenType, Token
from interpreter.utils.ast_printer import AstPrinter


class Interpreter(Visitor):
    def interpret(self, expr: Expr) -> None:
        try:
            val = self.evaluate(expr)
            print(self.stringify(val))
        except RuntimeException as e:
            Lox.runtime_error(e)

    def stringify(self, val: object) -> str:
        if val is None:
            return 'nil'
        return str(val)

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
            self._ensure_number_operands(expr.operator, left, right)
            return float(left) > float(right)
        if op_type == TokenType.GREATER_EQUAL:
            self._ensure_number_operands(expr.operator, left, right)
            return float(left) >= float(right)
        if op_type == TokenType.LESS:
            self._ensure_number_operands(expr.operator, left, right)
            return float(left) < float(right)
        if op_type == TokenType.LESS_EQUAL:
            self._ensure_number_operands(expr.operator, left, right)
            return float(left) <= float(right)

        if op_type == TokenType.PLUS:
            if isinstance(left, float) and isinstance(right, float):
                return float(left) + float(right)
            if isinstance(left, str) and isinstance(right, str):
                return str(left) + str(right)
            raise RuntimeException(expr.operator, 'Operands must be two numbers or two strings.')

        if op_type == TokenType.MINUS:
            self._ensure_number_operands(expr.operator, left, right)
            return float(left) - float(right)
        if op_type == TokenType.STAR:
            self._ensure_number_operands(expr.operator, left, right)
            return float(left) * float(right)
        if op_type == TokenType.SLASH:
            self._ensure_number_operands(expr.operator, left, right)
            return float(left) / float(right)

        raise RuntimeException(expr.operator, 'expect a binary expression')

    def visit_grouping(self, expr: Grouping) -> object:
        return self.evaluate(expr.expression)

    def visit_literal(self, expr: Literal) -> object:
        return expr.value

    def visit_unary(self, expr: Unary) -> object:
        right = self.evaluate(expr.right)

        op_type = expr.operator.type
        if op_type == TokenType.MINUS:
            self._ensure_number_operands(expr.operator, right)
            return -float(right)
        if op_type == TokenType.BANG:
            return self._is_true(right)

        raise RuntimeException(expr.operator, 'expect a unary expression')

    # 只有false和nil认为是假
    def _is_true(self, val: object) -> bool:
        if val is None:
            return False
        if isinstance(val, bool):
            return bool(val)
        return True

    # 等于运算支持所有类型的操作数
    def _is_equal(self, a: object, b: object) -> bool:
        if a is None and b is None:
            return True
        if a is None:
            return False
        return a == b

    def _ensure_number_operands(self, token: Token, *operands) -> None:
        for operand in operands:
            if not isinstance(operand, float):
                raise RuntimeException(token, 'Operand must be a number')


if __name__ == '__main__':
    scanner = Scanner('((1 + 2) * (-3)) + 4 / 0.5')
    tokens = scanner.scan_tokens()
    print(tokens)
    parser = Parser(tokens)
    expr = parser.parse()

    print(AstPrinter().build(expr))
    Interpreter().interpret(expr)

