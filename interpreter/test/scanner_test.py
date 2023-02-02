import unittest

from interpreter.scanner import Scanner


class ScannerTest(unittest.TestCase):

    def _run_test(self, source: str, expected: list[str], debug: bool = False) -> None:
        scanner = Scanner(source)
        tokens = scanner.scan_tokens()
        for i, token in enumerate(tokens):
            if debug:
                print(token)
            else:
                self.assertEqual(str(token), expected[i])

    def test_single_char_tokens(self):
        source = """
        * ; + - . , } { ()
        """
        expected = [
            'TokenType.STAR * None',
            'TokenType.SEMICOLON ; None',
            'TokenType.PLUS + None',
            'TokenType.MINUS - None',
            'TokenType.DOT . None',
            'TokenType.COMMA , None',
            'TokenType.RIGHT_BRACE } None',
            'TokenType.LEFT_BRACE { None',
            'TokenType.LEFT_PAREN ( None',
            'TokenType.RIGHT_PAREN ) None',
            'TokenType.EOF EOF None',
        ]
        self._run_test(source, expected)

    def test_two_char_tokens(self):
        source = """
            !
            !=
            = ==
            > >=
            <
            <=
        """
        expected = [
            'TokenType.BANG ! None',
            'TokenType.BANG_EQUAL != None',
            'TokenType.EQUAL = None',
            'TokenType.EQUAL_EQUAL == None',
            'TokenType.GREATER > None',
            'TokenType.GREATER_EQUAL >= None',
            'TokenType.LESS < None',
            'TokenType.LESS_EQUAL <= None',
            'TokenType.EOF EOF None',
        ]
        self._run_test(source, expected)

    def test_comment(self):
        source = """
            // hahahah
            /
        """
        expected = [
            'TokenType.SLASH / None',
            'TokenType.EOF EOF None',
        ]
        self._run_test(source, expected)

    def test_string(self):
        source = """
            "你好zzzz哈哈!!"
            
            "换
            行"
        """
        expected = [
            'TokenType.STRING "你好zzzz哈哈!!" 你好zzzz哈哈!!',
            'TokenType.STRING ' +
            """"换
            行" 换
            行""",
            'TokenType.EOF EOF None',
        ]
        self._run_test(source, expected, )

    def test_number(self):
        source = """
            123
            123.55
        """
        expected = [
            'TokenType.NUMBER 123 123.0',
            'TokenType.NUMBER 123.55 123.55',
            'TokenType.EOF EOF None',
        ]
        self._run_test(source, expected, )

    def test_identifier(self):
        source = """
            _name2
            ASUKA
            nil
            for
            true
        """
        expected = [
            'TokenType.IDENTIFIER _name2 None',
            'TokenType.IDENTIFIER ASUKA None',
            'TokenType.NIL nil None',
            'TokenType.FOR for None',
            'TokenType.TRUE true None',
            'TokenType.EOF EOF None',
        ]
        self._run_test(source, expected, )

    def test_unknown_character(self):
        source = """
            $
        """
        expected = [
            'TokenType.EOF EOF None',
        ]
        self._run_test(source, expected, )
        # show log the error

    def test_other(self):
        source = """
            // 计算 1 加到10
            var sum = 0
            for (var i = 1; i <= 10; i = i + 1) {
                sum = sum + i
            }
            print sum // 打印结果
        """
        expected = [
            'TokenType.VAR var None',
            'TokenType.IDENTIFIER sum None',
            'TokenType.EQUAL = None',
            'TokenType.NUMBER 0 0.0',
            'TokenType.FOR for None',
            'TokenType.LEFT_PAREN ( None',
            'TokenType.VAR var None',
            'TokenType.IDENTIFIER i None',
            'TokenType.EQUAL = None',
            'TokenType.NUMBER 1 1.0',
            'TokenType.SEMICOLON ; None',
            'TokenType.IDENTIFIER i None',
            'TokenType.LESS_EQUAL <= None',
            'TokenType.NUMBER 10 10.0',
            'TokenType.SEMICOLON ; None',
            'TokenType.IDENTIFIER i None',
            'TokenType.EQUAL = None',
            'TokenType.IDENTIFIER i None',
            'TokenType.PLUS + None',
            'TokenType.NUMBER 1 1.0',
            'TokenType.RIGHT_PAREN ) None',
            'TokenType.LEFT_BRACE { None',
            'TokenType.IDENTIFIER sum None',
            'TokenType.EQUAL = None',
            'TokenType.IDENTIFIER sum None',
            'TokenType.PLUS + None',
            'TokenType.IDENTIFIER i None',
            'TokenType.RIGHT_BRACE } None',
            'TokenType.PRINT print None',
            'TokenType.IDENTIFIER sum None',
            'TokenType.EOF EOF None',
        ]
        self._run_test(source, expected, )
