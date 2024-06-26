from __future__ import annotations
import time
from abc import ABCMeta, abstractmethod

from interpreter.env import Env
from interpreter.error import ReturnException, RuntimeException
from interpreter.interpreter_ import Interpreter
from interpreter.stmt import Function
from interpreter.token_ import Token


class Callable(metaclass=ABCMeta):
    @abstractmethod
    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        pass

    # 形参个数
    @abstractmethod
    def arity(self) -> int:
        pass


# lox类再python中的表示
class LoxClass(Callable):
    name: str
    methods: dict[str, LoxFunction]
    super_class: LoxClass

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        instance = LoxInstance(self)
        # 调用构造函数
        initializer = self.find_method('init')
        if initializer is not None:
            initializer.bind(instance).call(interpreter, arguments)

        return instance

    def arity(self) -> int:
        initializer = self.find_method('init')
        if initializer is not None:
            return initializer.arity()
        return 0

    def find_method(self, name: str) -> LoxFunction:
        if name in self.methods.keys():
            return self.methods[name]

        if self.super_class is not None:
            return self.super_class.find_method(name)

        return None

    def __init__(self, name, super_class, methods):
        self.name = name
        self.methods = methods
        self.super_class = super_class

    def __repr__(self):
        return self.name


# lox类的实例
class LoxInstance:
    klass: LoxClass
    fields: dict[str, object]

    def __init__(self, klass):
        self.klass = klass
        self.fields = {}

    def get(self, name: Token) -> object:
        if name.lexeme in self.fields.keys():
            return self.fields[name.lexeme]

        method = self.klass.find_method(name.lexeme)
        if method is not None:
            return method.bind(self)

        # todo 这种报错可以也考虑放到resolver中去, 不要等到运行时再报错?
        raise RuntimeException(name, f"undefined property '{name.lexeme}'")

    def set(self, name: Token, value: object) -> None:
        self.fields[name.lexeme] = value

    def __repr__(self):
        return f'{self.klass.name} instance'


# lox函数在python中的表示, 它会绑定一个名字存在环境中
class LoxFunction(Callable):
    declaration: Function
    closure_env: Env
    is_initializer: bool

    def __init__(self, declaration, env, is_initializer):
        self.declaration = declaration
        # 在创建当前这个函数的同时 保存这个函数所在的环境
        self.closure_env = env
        # 是否是构造方法
        self.is_initializer = is_initializer

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        # 每执行一个函数 都需要一个新的环境 来保存当前函数的局部变量
        env = Env(self.closure_env)
        for i, param in enumerate(self.declaration.params):
            arg = arguments[i]
            env.define(param.lexeme, arg)

        try:
            interpreter.execute_block(self.declaration.body, env)
        except ReturnException as e:
            # 如果是构造方法 永远返回this
            if self.is_initializer:
                return self.closure_env.get_at(0, 'this')

            return e.value

        # 手动调用构造方法 也返回this
        if self.is_initializer:
            return self.closure_env.get_at(0, 'this')

        return None

    def arity(self) -> int:
        return len(self.declaration.params)

    # 用来给当前方法绑定this
    def bind(self, instance: LoxInstance) -> LoxFunction:
        env = Env(self.closure_env)
        env.define('this', instance)
        return LoxFunction(self.declaration, env, self.is_initializer)

    def __repr__(self):
        return f'<fn {self.declaration.name.lexeme}>'


# 内置函数
class Clock(Callable):

    def call(self, interpreter: Interpreter, arguments: list[object]) -> object:
        return time.time()

    def arity(self) -> int:
        return 0

    def __repr__(self):
        return '<native fn>'
