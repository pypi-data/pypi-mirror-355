from antlr4.CommonTokenStream import CommonTokenStream
from antlr4.InputStream import InputStream

from stgem.monitor.pystl.stlLexer import stlLexer as Lexer
from stgem.monitor.pystl.stlParser import stlParser as Parser
from stgem.monitor.pystl.visitor import stlParserVisitor as Visitor

def parse(phi):
    """ parses a string containing a formula into an equivalent STL structure

    """
    input_stream = InputStream(phi)

    lexer = Lexer(input_stream)
    stream = CommonTokenStream(lexer)

    parser = Parser(stream)
    tree = parser.stlformula()
    visitor = Visitor()

    return visitor.visit(tree)  # type: ignore

