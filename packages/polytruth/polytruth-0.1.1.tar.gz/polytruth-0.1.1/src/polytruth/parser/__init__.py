from typing import Optional, Union
from ply import lex, yacc
import os
import logging
from types import MappingProxyType

from ..core import And, Or, Implies, Equiv,Not, Var

from .. import LogicSystem
class __LogicParser:
    """Parser for logical expressions using PLY (lex/yacc)

    Attributes:
        __system__: Reference to the logic system for variable creation
        lexer: Lexical analyzer instance
        parser: Syntax parser instance
        errors: List of accumulated parsing errors
        current_file: Current file being parsed (for error reporting)
    """
    def __init__(self,system:LogicSystem) -> None:
        """Initialize parser with associated logic system

        Args:
            system: The logic system to use for variable creation
        """
        self.__system__:LogicSystem=system
        self.lexer = lex.lex(module=self)
        self.parser = yacc.yacc(module=self,tabmodule="logic_parsetab")
        self.errors = []
        self.current_file = None
    # Token definitions for lexer
    tokens = (
            'FORALL', 'EXISTS',       # Quantifiers: ∀/forall, ∃/exists
            'NOT', 'AND', 'OR',       # Logical operators: ¬/~, ∧/&//\\, ∨/|/\\/
            'IMPLIES', 'IFF',         # Implications: →/->, ↔/<->
            'LPAREN', 'RPAREN',      # Parentheses: ( )
            'COMMA', 'COLON',        # Punctuation: , :
            'INDENT',     # Identifiers: alphanum, alphanum(
        )

 # Token regex rules
    def t_INDENT(self, t):
        r'[a-zA-Z0-9_]+'  # Match alphanumeric identifiers
        return t

    def t_PREDICATE(self, t):
        r'[a-zA-Z0-9_]+\('  # Match predicate names (ending with '(')
        t.value = t.value[:-1]  # Remove trailing '('
        return t

    # Operator definitions
    t_FORALL = r'∀|forall'
    t_EXISTS = r'∃|exists'
    t_NOT = r'¬|~'
    t_AND = r'∧|&|/\\'
    t_OR = r'∨|\||\\/'
    t_IMPLIES = r'→|->'
    t_IFF = r'↔|<->'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_COMMA = r','
    t_COLON = r':'
    t_ignore = ' \t\n'  # Ignore whitespace

    def t_error(self, t):
        """Handle lexer errors"""
        msg = f"Illegal character: '{t.value[0]}'"
        logging.error(msg)
        self.errors.append(msg)
        t.lexer.skip(1)

    # Parser precedence rules (from lowest to highest)
    precedence = (
        ('right', 'IFF'),         # ↔ is right-associative
        ('right', 'IMPLIES'),     # → is right-associative
        ('left', 'OR'),            # ∨ is left-associative
        ('left', 'AND'),           # ∧ is left-associative
        ('right', 'NOT'),          # ¬ is right-associative
        ('right', 'FORALL', 'EXISTS'),  # Quantifiers have highest precedence
    )

    # Grammar rules
    def p_label(self, p):
        'label : INDENT COLON expression'
        p[0] = p[3]  # Return parsed expression
        # Add rule to logic system with given label
        self.__system__.add_rule(p[1], p[3])

    def p_expression_quantifier(self, p):
        """
        expression : FORALL INDENT expression
                   | EXISTS INDENT expression
        """
        raise NotImplementedError("Quantifiers are not supported yet.")

    def p_expression_and(self, p):
        'expression : expression AND expression'
        p[0] = And(p[1], p[3])  # Create AND node

    def p_expression_or(self, p):
        'expression : expression OR expression'
        p[0] = Or(p[1], p[3])  # Create OR node

    def p_expression_implies(self, p):
        'expression : expression IMPLIES expression'
        p[0] = Implies(p[1], p[3])  # Create IMPLIES node

    def p_expression_iff(self, p):
        'expression : expression IFF expression'
        p[0] = Equiv(p[1], p[3])  # Create EQUIV node

    def p_expression_not(self, p):
        'expression : NOT expression'
        p[0] = Not(p[2])  # Create NOT node

    def p_expression_group(self, p):
        'expression : LPAREN expression RPAREN'
        p[0] = p[2]  # Return inner expression

    def p_expression_predicate(self, p):
        'expression : INDENT LPAREN term_list RPAREN'
        # Create variable with formatted name "pred(arg1,arg2,...)"
        p[0] = self.__system__.new_variable(f"{p[1]}({','.join(p[3])})")

    def p_expression_atomic(self, p):
        'expression : INDENT'
        p[0] = self.__system__.new_variable(p[1])  # Create variable node

    def p_term_list(self, p):
        """term_list : term
                    | term COMMA term_list
        """
        if len(p) == 2:  # Single term
            p[0] = [p[1]]
        else:  # Multiple terms
            p[0] = [p[1]] + p[3]  # Combine terms

    def p_term_INDENT(self, p):
        'term : INDENT'
        p[0] = p[1]  # Return identifier string

    def p_error(self, p):
        """Handle parser syntax errors"""
        if p:
            msg = f"Syntax error at '{p.value}' (line: {p.lineno}, position: {p.lexpos})"
        else:
            msg = "Syntax error: Unexpected end of input"
        logging.error(msg)
        self.errors.append(msg)

    def parse_single(self, expression: str) -> Optional[Union[And, Or, Implies, Equiv, Not, Var]]:
        """Parse a single logical expression

        Args:
            expression: String containing logical expression

        Returns:
            Parsed AST node or None if error occurs
        """
        self.errors.clear()
        try:
            return self.parser.parse(expression, lexer=self.lexer)
        except Exception as e:
            self.errors.append(f"Parsing exception: {str(e)}")
            return None

    def parse_string(self, input_str: str) -> None:
        """Parse multi-expression input string

        Supports:
          - One expression per line
          - Semicolon-separated expressions
          - #-prefixed comment lines

        Args:
            input_str: Input string containing expressions
        """
        self.errors.clear()
        lines = input_str.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # Skip empty lines and comments

            # Split semicolon-separated expressions
            expressions = [e.strip() for e in line.split(';') if e.strip()]
            for expr in expressions:
                try:
                    self.parser.parse(expr, lexer=self.lexer)
                except Exception as e:
                    self.errors.append(f"Expression '{expr}' parse failed: {str(e)}")

    def parse_file(self, file_path: str) -> None:
        """Parse logical expressions from file

        Args:
            file_path: Path to file containing expressions
        """
        self.current_file = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.parse_string(content)
        except Exception as e:
            self.errors.append(f"File read error: {str(e)}")
        finally:
            self.current_file = None

def parse_file(file_path,system:LogicSystem)->list:
    """Parse logic rules from file into a LogicSystem

    Args:
        file_path: Path to source file
        system: Target logic system instance
    Returns:
        List of error messages
    """
    parser=__LogicParser(system)
    parser.parse_file(file_path)
    return parser.errors

def parse_string(input_str:str,system:LogicSystem)->list:
    """Parse multi-expression input string

    Supports:
      - One expression per line
      - Semicolon-separated expressions
      - #-prefixed comment lines

    Args:
        input_str: Input string containing expressions
        system: Target logic system instance
    Returns:
        List of error messages
    """
    parser=__LogicParser(system)
    parser.parse_string(input_str)
    return parser.errors
