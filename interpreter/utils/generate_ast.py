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

    for type in types:
        classname, fields_desc = type.strip().split(':')
        type_text = define_type(base_classname, classname.strip(), fields_desc.strip())
        types_text += type_text

    gen_date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    ast = f"""
# generate time: {gen_date}
from abc import abstractmethod, ABCMeta
from interpreter.token import Token

# 所有表达式的抽象父类
class Expr(metaclass=ABCMeta):
    pass

{types_text}
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

    """
一个例子

class Binary(Expr):
left: Expr
operator: Token
right: Expr

def __init__(self, left: Expr, operator: Token, right: Expr):
    self.left = left
    self.operator = operator
    self.right = right
    """

    ast = f"""
class {classname}({base_classname}):
{fields_text}
    def __init__(self, {init_params_text}):
{init_body_text}
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
