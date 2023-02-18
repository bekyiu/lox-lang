TAB_TEXT = '    '


def define_ast(base_classname: str, types: list[str]) -> str:
    import datetime
    types_text = ''
    visitor_methods_text = ''
    for type in types:
        classname, fields_desc = type.strip().split(':')
        types_text += define_type(base_classname, classname.strip(), fields_desc.strip())
        visitor_methods_text += define_visitor(base_classname, classname.strip())

    gen_date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
    ast = f"""
# generate time: {gen_date}
from __future__ import annotations
from abc import abstractmethod, ABCMeta
from interpreter.token_ import Token

class {base_classname}(metaclass=ABCMeta):
    @abstractmethod
    def accept(self, visitor: {base_classname}Visitor) -> object:
        pass

class {base_classname}Visitor(metaclass=ABCMeta):
{visitor_methods_text}
{types_text}
    """

    return ast


def define_visitor(base_classname: str, classname: str) -> str:
    ast = f"""
    @abstractmethod
    def visit_{classname.lower()}(self, {base_classname.lower()}: {classname}) -> object:
        pass
    """
    return ast


def define_type(base_classname: str, classname: str, fields_desc: str) -> str:
    fields = fields_desc.strip().split(',')

    fields_text = ''
    init_params_text = ''
    init_body_text = ''

    for f in fields:
        f = f.strip()
        if f == '':
            init_body_text = f'{TAB_TEXT}{TAB_TEXT}pass'
            continue
        type, name = f.split(' ')

        fields_text += f'{TAB_TEXT}{name}: {type}\n'
        init_params_text += f'{name}: {type}, '
        init_body_text += f'{TAB_TEXT}{TAB_TEXT}self.{name} = {name}\n'

    ast = f"""
class {classname}({base_classname}):
{fields_text}
    def __init__(self, {init_params_text}):
{init_body_text}
    def accept(self, visitor: {base_classname}Visitor) -> object:
        return visitor.visit_{classname.lower()}(self)
    """
    return ast


if __name__ == '__main__':
    ast = define_ast('Expr', [
        # 子类名: 字段类型 字段名称, ...
        "Assign   : Token name, Expr value",
        "Binary   : Expr left, Token operator, Expr right",
        "Call     : Expr callee, Token paren, list[Expr] arguments",
        "Get      : Expr object, Token name",
        "Set      : Expr object, Token name, Expr value",
        "Grouping : Expr expression",
        "Literal  : object value",
        "Logical  : Expr left, Token operator, Expr right",
        "Unary    : Token operator, Expr right",
        "Variable : Token name",
    ])

    path = '../expr.py'
    with open(path, 'w') as f:
        f.write(ast)

    ast = define_ast('Stmt', [
        # 子类名: 字段类型 字段名称, ...
        "Block      : list[Stmt] statements",
        "Class      : Token name, list[Function] methods",
        "Expression : Expr expression",
        "Function   : Token name, list[Token] params, list[Stmt] body",
        "Break      : Token break_",
        "Continue   : Token continue_",
        "If         : Expr condition, Stmt then_branch, Stmt else_branch",
        "Print      : Expr expression",
        "While      : Expr condition, Stmt body",
        "Return     : Token keyword, Expr value",
        "Var        : Token name, Expr initializer",
    ])

    path = '../stmt.py'

    # with open(path, 'w') as f:
    #     f.write(ast)

    print('ok!!')
