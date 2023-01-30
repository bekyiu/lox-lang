"""
expression     → literal
               | unary
               | binary
               | grouping ;

literal        → NUMBER | STRING | "true" | "false" | "nil" ;
grouping       → "(" expression ")" ;
unary          → ( "-" | "!" ) expression ;
binary         → expression operator expression ;
operator       → "==" | "!=" | "<" | "<=" | ">" | ">="
               | "+"  | "-"  | "*" | "/" ;
"""

TAB_TEXT = '    '


def define_ast(base_classname: str, types: list[str]) -> str:
    import datetime
    types_text = ''
    visitor_methods_text = ''
    for type in types:
        classname, fields_desc = type.strip().split(':')
        types_text += define_type(base_classname, classname.strip(), fields_desc.strip())
        visitor_methods_text += define_visitor(classname.strip())

    gen_date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    ast = f"""
# generate time: {gen_date}
from __future__ import annotations
from abc import abstractmethod, ABCMeta
from interpreter.token import Token

class Expr(metaclass=ABCMeta):
    @abstractmethod
    def accept(self, visitor: Visitor) -> object:
        pass

class Visitor(metaclass=ABCMeta):
{visitor_methods_text}
{types_text}
    """

    return ast


def define_visitor(classname: str) -> str:
    ast = f"""
    @abstractmethod
    def visit_{classname.lower()}(self, expr: {classname}) -> object:
        pass
    """
    return ast


def define_type(base_classname: str, classname: str, fields_desc: str) -> str:
    fields = fields_desc.strip().split(',')

    fields_text = ''
    init_params_text = ''
    init_body_text = ''

    for f in fields:
        type, name = f.strip().split(' ')

        fields_text += f'{TAB_TEXT}{name}: {type}\n'
        init_params_text += f'{name}: {type}, '
        init_body_text += f'{TAB_TEXT}{TAB_TEXT}self.{name} = {name}\n'

    ast = f"""
class {classname}({base_classname}):
{fields_text}
    def __init__(self, {init_params_text}):
{init_body_text}
    def accept(self, visitor: Visitor) -> object:
        return visitor.visit_{classname.lower()}(self)
    """
    return ast


if __name__ == '__main__':
    ast = define_ast('Expr', [
        # 子类名: 字段类型 字段名称, ...
        "Binary   : Expr left, Token operator, Expr right",
        "Grouping : Expr expression",
        "Literal  : object value",
        "Unary    : Token operator, Expr right",
    ])

    path = '/Users/bekyiu/dev/pythonProject/lox-lang/interpreter/expr.py'
    with open(path, 'w') as f:
        f.write(ast)

    print('ok!!')