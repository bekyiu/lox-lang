from enum import unique, Enum

from interpreter.expr import ExprVisitor, Variable, Unary, Logical, Literal, Grouping, Call, Binary, Assign, Expr, Get, \
    Set, This
from interpreter.lox import Lox
from interpreter.stmt import StmtVisitor, Var, Return, While, Print, If, Continue, Break, Function, Expression, Block, \
    Stmt, Class
from interpreter.token_ import Token
from interpreter.interpreter_ import Interpreter


@unique
class FunctionType(Enum):
    NONE = 0
    FUNCTION = 1
    METHOD = 2
    INITIALIZER = 3


@unique
class ClassType(Enum):
    NONE = 0
    CLASS = 1


# 静态分析 变量绑定
class Resolver(ExprVisitor, StmtVisitor):
    interpreter: Interpreter
    # 作用域map中与key相关联的值代表的是我们是否已经结束了对变量初始化式的解析
    scope_stack: list[dict[str, bool]]
    current_function: FunctionType
    current_class: ClassType

    def __init__(self, interpreter):
        self.interpreter = interpreter
        self.scope_stack = []
        self.current_function = FunctionType.NONE
        self.current_class = ClassType.NONE

    def resolve(self, statements: list[Stmt]) -> None:
        for stmt in statements:
            self._resolve_stmt(stmt)

    def _resolve_stmt(self, statement: Stmt) -> None:
        statement.accept(self)

    def _resolve_expr(self, expression: Expr) -> None:
        expression.accept(self)

    def _begin_scope(self) -> None:
        self.scope_stack.append({})

    def _end_scope(self) -> None:
        self.scope_stack.pop()

    # 声明变量
    def _declare(self, name: Token) -> None:
        # 忽略全局变量
        if len(self.scope_stack) == 0:
            return
        scope = self.scope_stack[-1]
        # 同一个作用域中禁止申明同名变量
        if name.lexeme in scope.keys():
            Lox.error(token=name, message='already variable with this name in this scope.')

        scope[name.lexeme] = False

    # 变量定义
    def _define(self, name: Token) -> None:
        if len(self.scope_stack) == 0:
            return
        scope = self.scope_stack[-1]
        scope[name.lexeme] = True

    # 计算在当前作用域和变量定义的作用域之间隔着多少层作用域
    # 所以，如果在当前作用域中找到该变量，则传入0；如果在紧邻的外网作用域中找到，则传1
    def _resolve_local(self, expr: Expr, name: Token) -> None:
        i = len(self.scope_stack) - 1
        while i >= 0:
            scope = self.scope_stack[i]
            if name.lexeme in scope.keys():
                self.interpreter.resolve(expr, len(self.scope_stack) - 1 - i)
                return
            i -= 1

    def _resolve_function(self, stmt: Function, type: FunctionType) -> None:
        # 表明进入了函数
        pre_func = self.current_function
        self.current_function = type

        self._begin_scope()
        for param in stmt.params:
            self._declare(param)
            self._define(param)
        # 静态分析中 立即遍历了函数体
        self.resolve(stmt.body)
        self._end_scope()

        self.current_function = pre_func

    def visit_assign(self, expr: Assign) -> object:
        self._resolve_expr(expr.value)
        self._resolve_local(expr, expr.name)
        return None

    def visit_binary(self, expr: Binary) -> object:
        self._resolve_expr(expr.left)
        self._resolve_expr(expr.right)
        return None

    def visit_call(self, expr: Call) -> object:
        self._resolve_expr(expr.callee)
        for arg in expr.arguments:
            self._resolve_expr(arg)
        return None

    def visit_get(self, expr: Get) -> object:
        # 属性是动态查找的, 所以不管点右边的名称
        self._resolve_expr(expr.object)
        return None

    def visit_set(self, expr: Set) -> object:
        self._resolve_expr(expr.value)
        self._resolve_expr(expr.object)
        return None

    def visit_grouping(self, expr: Grouping) -> object:
        self._resolve_expr(expr.expression)
        return None

    def visit_literal(self, expr: Literal) -> object:
        return None

    def visit_logical(self, expr: Logical) -> object:
        self._resolve_expr(expr.left)
        self._resolve_expr(expr.right)
        return None

    def visit_this(self, expr: This) -> object:
        if self.current_class == ClassType.NONE:
            Lox.error(token=expr.keyword, message=f"can not use 'this' outside of class")
            return None

        # 只要遇到this表达式（至少是在方法内部），它就会解析为一个“局部变量”
        # 该变量定义在方法体块之外的隐含作用域中。
        self._resolve_local(expr, expr.keyword)
        return None

    def visit_unary(self, expr: Unary) -> object:
        self._resolve_expr(expr.right)
        return None

    def visit_variable(self, expr: Variable) -> object:
        if len(self.scope_stack) != 0 and expr.name.lexeme in self.scope_stack[-1].keys():
            var = self.scope_stack[-1][expr.name.lexeme]
            if not var:
                Lox.error(token=expr.name, message='Can not read local variable in its own initializer')

        self._resolve_local(expr, expr.name)
        return None

    def visit_class(self, stmt: Class) -> object:
        pre_class = self.current_class
        self.current_class = ClassType.CLASS

        self._declare(stmt.name)
        self._declare(stmt.name)
        if stmt.super_class is not None:
            if stmt.name.lexeme == stmt.super_class.name.lexeme:
                Lox.error(token=stmt.super_class.name, message='a class can not inherit from itself')

            self._resolve_expr(stmt.super_class)

        self._begin_scope()
        # 声明this
        # 解释器是在执行get表达式的时候才来创建的env
        self.scope_stack[-1]['this'] = True
        for m in stmt.methods:
            func_type = FunctionType.INITIALIZER if m.name.lexeme == 'init' else FunctionType.METHOD
            self._resolve_function(m, func_type)
        self._end_scope()

        self.current_class = pre_class
        return None

    def visit_block(self, stmt: Block) -> object:
        self._begin_scope()
        self.resolve(stmt.statements)
        self._end_scope()
        return None

    def visit_expression(self, stmt: Expression) -> object:
        self._resolve_expr(stmt.expression)
        return None

    def visit_function(self, stmt: Function) -> object:
        self._declare(stmt.name)
        self._define(stmt.name)
        self._resolve_function(stmt, FunctionType.FUNCTION)
        return None

    def visit_break(self, stmt: Break) -> object:
        return None

    def visit_continue(self, stmt: Continue) -> object:
        pass

    def visit_if(self, stmt: If) -> object:
        self._resolve_expr(stmt.condition)
        self._resolve_stmt(stmt.then_branch)
        if stmt.else_branch is not None:
            self._resolve_stmt(stmt.else_branch)
        return None

    def visit_print(self, stmt: Print) -> object:
        self._resolve_expr(stmt.expression)
        return None

    def visit_while(self, stmt: While) -> object:
        self._resolve_expr(stmt.condition)
        self._resolve_stmt(stmt.body)
        return None

    def visit_return(self, stmt: Return) -> object:
        # return 必须要在函数中
        if self.current_function == FunctionType.NONE:
            Lox.error(token=stmt.keyword, message='can not return from top level code')

        if stmt.value is not None:
            if self.current_function == FunctionType.INITIALIZER:
                Lox.error(token=stmt.keyword, message='can not return a value from initializer')
            self._resolve_expr(stmt.value)
        return None

    # 声明变量 在当前作用域中添加一项
    def visit_var(self, stmt: Var) -> None:
        self._declare(stmt.name)
        if stmt.initializer is not None:
            self._resolve_expr(stmt.initializer)
        self._define(stmt.name)
