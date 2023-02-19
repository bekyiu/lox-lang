# todo
from interpreter.interpreter_ import Interpreter
from interpreter.parser import Parser
from interpreter.resolver import Resolver
from interpreter.scanner import Scanner


def test1() -> str:
    code = """
    fun makeCounter() {
      var i = 0;
      fun count() {
        i = i + 1;
        print i;
      }

      return count;
    }
    var counter = makeCounter();
    counter();
    counter();
        """

    code = """
    fun scope(a) {
      var a = "local";
      print a;
    }

    scope(1);

        """

    code = """
    fun fib(n) {
      if (n <= 1) return n;
      return fib(n - 2) + fib(n - 1);
    }

    for (var i = 0; i < 20; i = i + 1) {
      print fib(i);
    }
        """

    code = """
    fun A() {
        var a = 99;
        fun B() {
            fun C() {
                a = a + 1;
                print a;
            }
            return C;
        }
        return B;
    }

    A()()();
    """

    code = """
    fun test() {
                var a = 10;
                print a;
                return a;
    }
    test();
    
    """
    return code


def test_class_decl() -> str:
    code = """
    class Group {
        serveOn() {
            return "Scones";
        }
    }
    
    print Group; // Prints "Group".
    var g = Group();
    print g; // Group instance
    """
    return code


def test_get_set() -> str:
    code = """
    class Group {
        serveOn() {
            return "Scones";
        }
    }

    print Group; // Prints "Group".

    var g = Group();
    g.name = "Nogizaka 46";
    g.age = 10;

    print g; // Group instance
    print g.name;
    print g.age;
    """
    return code


def test_method() -> str:
    code = """
    class Group {
        add(a, b) {
            print "add exec";
            return a + b;   
        }
    }


    var g = Group();
    var ret = g.add(3.3, 2);
    print ret;
    """
    return code


def test_this() -> str:
    code = """
    class Group {
        add(a, b) {
            print this.name;
            return a + b;   
        }
    }


    var g = Group();
    g.name = "sb";
    var ret = g.add(3.3, 2);
    print ret;
    """

    code = """
    class User {
        new(name, age) {
            this.name = name;
            this.age = age;
            return this;
        }
    
        doWork() {
            print clock();
            print this.name + " is doing some work";
        }
    }
    
    var u = User().new("wyc", 10);
    u.doWork();
    """
    return code


def test_init():
    code = """
    class User {
        init(name, age) {
            this.name = name;
            this.age = age;
        }

        doWork() {
            print clock();
            print this.name + " " + this.age + " is doing some work";
        }
    }

    var u = User("haha", 10);
    u.doWork();
    """
    return code


def test_init_error():
    code = """
    class User {
        init(name, age) {
            this.name = name;
            this.age = age;
            // return 1;
        }

        doWork() {
            print clock();
            print this.name + " " + this.age + " is doing some work";
        }
    }

    var u = User("hahaxx", 10);
    var u2 = u.init("zz", 22);
    print u2;
    u.doWork();
    u2.doWork();
    print u == u2;
    """
    return code


if __name__ == '__main__':
    scanner = Scanner(test_init_error())
    tokens = scanner.scan_tokens()
    print(tokens)
    parser = Parser(tokens)
    stmts = parser.parse()

    # print(AstPrinter().build(expr))
    interpreter = Interpreter()
    resolver = Resolver(interpreter)
    resolver.resolve(stmts)
    print(interpreter.local_map)
    print('================')
    interpreter.interpret(stmts)
