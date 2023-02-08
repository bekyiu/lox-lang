from interpreter.env import Env
from interpreter.error import RuntimeException
from interpreter.expr import ExprVisitor, Expr, Binary, Grouping, Literal, Unary, Variable, Assign, Logical
from interpreter.lox import Lox
from interpreter.parser import Parser
from interpreter.scanner import Scanner
from interpreter.stmt import StmtVisitor, Print, Expression, Stmt, Var, Block, If, While, Continue, Break
from interpreter.token_ import TokenType, Token


class Interpreter(ExprVisitor, StmtVisitor):
    env: Env

    def __init__(self):
        self.env = Env()

    def interpret(self, stmts: list[Stmt]) -> None:
        try:
            for stmt in stmts:
                self.execute(stmt)
        except RuntimeException as e:
            Lox.runtime_error(e)

    def execute(self, stmt: Stmt) -> None:
        stmt.accept(self)

    def visit_expression(self, stmt: Expression) -> object:
        self.evaluate(stmt.expression)
        return None

    # 这里可以考虑把这种只有一个关键字的语句抽象到同一个ast节点中
    def visit_break(self, stmt: Break) -> None:
        raise RuntimeException(stmt.break_, 'break control flow')

    def visit_continue(self, stmt: Continue) -> None:
        pass

    def visit_while(self, stmt: While) -> object:
        while self._is_true(self.evaluate(stmt.condition)):
            try:
                self.execute(stmt.body)
            except RuntimeException as e:
                # 这个issue讨论了break和continue的实现
                # https://github.com/munificent/craftinginterpreters/issues/119
                if e.token.type == TokenType.BREAK:
                    print(e.msg + ',zz')
                    break
        return None

    def visit_if(self, stmt: If) -> object:
        cond = self._is_true(self.evaluate(stmt.condition))
        if cond:
            self.execute(stmt.then_branch)
            return None
        if stmt.else_branch is not None:
            self.execute(stmt.else_branch)
        return None

    def visit_print(self, stmt: Print) -> object:
        val = self.evaluate(stmt.expression)
        print(self.stringify(val))
        return None

    def visit_var(self, stmt: Var) -> object:
        val = None
        if stmt.initializer is not None:
            val = self.evaluate(stmt.initializer)
        self.env.define(stmt.name.lexeme, val)
        return None

    def visit_block(self, stmt: Block) -> object:
        self.execute_block(stmt.statements, Env(self.env))
        return None

    def execute_block(self, stmts: list[Stmt], env: Env) -> None:
        pre_env = self.env
        try:
            self.env = env
            for stmt in stmts:
                self.execute(stmt)
        finally:
            self.env = pre_env

    def stringify(self, val: object) -> str:
        if val is None:
            return 'nil'
        if isinstance(val, bool):
            return str(val).lower()
        return str(val)

    def evaluate(self, expr: Expr) -> object:
        return expr.accept(self)

    def visit_assign(self, expr: Assign) -> object:
        val = self.evaluate(expr.value)
        self.env.assign(expr.name, val)
        # 赋值是表达式 要返回值的
        return val

    def visit_logical(self, expr: Logical) -> object:
        left = self.evaluate(expr.left)
        # 短路逻辑
        if expr.operator.type == TokenType.OR:
            if self._is_true(left):
                return left
        else:
            if not self._is_true(left):
                return left
        return self.evaluate(expr.right)

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
            return not self._is_true(right)

        raise RuntimeException(expr.operator, 'expect a unary expression')

    def visit_variable(self, expr: Variable) -> object:
        return self.env.get(expr.name)

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
    scanner = Scanner("""
        var sum = 0;
        
        for (var i = 0; i <= 100; i = i + 1) {
            sum = sum + i;
            if (sum > 100) {
                break;
            }
        }
        print sum;
    """)
    tokens = scanner.scan_tokens()
    print(tokens)
    parser = Parser(tokens)
    stmts = parser.parse()

    # print(AstPrinter().build(expr))
    Interpreter().interpret(stmts)
