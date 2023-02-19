from interpreter.env import Env
from interpreter.error import RuntimeException, BreakException, ReturnException
from interpreter.expr import ExprVisitor, Expr, Binary, Grouping, Literal, Unary, Variable, Assign, Logical, Call, Get, \
    Set
from interpreter.lox import Lox
from interpreter.stmt import StmtVisitor, Print, Expression, Stmt, Var, Block, If, While, Continue, Break, Function, \
    Return, Class
from interpreter.token_ import TokenType, Token


class Interpreter(ExprVisitor, StmtVisitor):
    outermost: Env
    env: Env
    local_map: dict[Expr, int]

    def __init__(self):
        from interpreter.callable import Clock
        # 最外层环境
        self.outermost = Env()
        # 当前所在环境
        self.env = self.outermost
        # 注册内置函数
        self.outermost.define('clock', Clock())
        # 在当前作用域和变量定义的作用域之间隔着多少层作用域
        self.local_map = {}

    def resolve(self, expr: Expr, depth: int) -> None:
        self.local_map[expr] = depth

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

    def visit_return(self, stmt: Return) -> None:
        value = None
        if stmt.value is not None:
            value = self.evaluate(stmt.value)

        raise ReturnException(value)

    # 这里可以考虑把这种只有一个关键字的语句抽象到同一个ast节点中
    def visit_break(self, stmt: Break) -> None:
        raise BreakException()

    def visit_continue(self, stmt: Continue) -> None:
        pass

    def visit_while(self, stmt: While) -> object:
        while self._is_true(self.evaluate(stmt.condition)):
            try:
                self.execute(stmt.body)
            except BreakException as e:
                # 这个issue讨论了break和continue的实现
                # https://github.com/munificent/craftinginterpreters/issues/119
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

    def visit_class(self, stmt: Class) -> object:
        from interpreter.callable import LoxClass, LoxFunction

        self.env.define(stmt.name.lexeme, None)
        methods = {}
        for m in stmt.methods:
            func = LoxFunction(m, self.env)
            methods[m.name.lexeme] = func

        klass = LoxClass(stmt.name.lexeme, methods)
        # 这个二阶段的变量绑定过程允许在类的方法中引用其自身
        self.env.assign(stmt.name, klass)
        return None

    def visit_function(self, stmt: Function) -> object:
        from interpreter.callable import LoxFunction
        func = LoxFunction(stmt, self.env)
        self.env.define(stmt.name.lexeme, func)
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

        if expr in self.local_map.keys():
            distance = self.local_map[expr]
            self.env.assign_at(distance, expr.name, val)
        else:
            self.outermost.assign(expr.name, val)
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
            if (not isinstance(left, float)) and (not isinstance(left, str)):
                raise RuntimeException(expr.operator, 'left operand must be number or string.')

            if (not isinstance(right, float)) and (not isinstance(right, str)):
                raise RuntimeException(expr.operator, 'right operand must be number or string.')

            if isinstance(left, float) and isinstance(right, float):
                return float(left) + float(right)

            return str(left) + str(right)

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

    def visit_call(self, expr: Call) -> object:
        # expr.callee是一个variable 所以会拿到env中注册好的函数
        callee = self.evaluate(expr.callee)
        args = []
        for a in expr.arguments:
            args.append(self.evaluate(a))

        from interpreter.callable import Callable
        if not isinstance(callee, Callable):
            raise RuntimeException(expr.paren, 'can only call function and class')

        func: Callable = callee
        if len(args) != func.arity():
            raise RuntimeException(expr.paren, f'expected {func.arity()} arguments but got {len(args)}')

        return func.call(self, args)

    def visit_get(self, expr: Get) -> object:
        obj = self.evaluate(expr.object)
        from interpreter.callable import LoxInstance
        if not isinstance(obj, LoxInstance):
            raise RuntimeException(expr.name, 'only instance have properties')

        # obj: LoxInstance = obj
        return obj.get(expr.name)

    def visit_set(self, expr: Set) -> object:
        obj = self.evaluate(expr.object)
        from interpreter.callable import LoxInstance
        if not isinstance(obj, LoxInstance):
            raise RuntimeException(expr.name, 'only instance have fields')

        value = self.evaluate(expr.value)
        obj.set(expr.name, value)
        return value

    def visit_variable(self, expr: Variable) -> object:
        return self._lookup_variable(expr.name, expr)

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

    def _lookup_variable(self, name: Token, expr: Expr) -> object:
        if expr in self.local_map.keys():
            distance = self.local_map[expr]
            return self.env.get_at(distance, name.lexeme)
        return self.outermost.get(name)
