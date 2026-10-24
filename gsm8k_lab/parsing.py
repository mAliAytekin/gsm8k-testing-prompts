"""Strict, exact numeric parsing and bounded arithmetic. No eval or exec."""
import ast
import re
from decimal import Decimal, InvalidOperation
from fractions import Fraction


class FormatError(ValueError):
    pass


class ResourceError(ValueError):
    pass


NUMBER = r'[+-]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)'


def numeric(text):
    if not isinstance(text, str) or len(text) > 200:
        raise FormatError('Numeric text required, maximum 200 characters')
    text = text.strip()
    # A single leading currency symbol is allowed; percentages/units are not.
    if text[:1] in ('$', '£', '€'):
        text = text[1:].strip()
    parts = re.fullmatch(rf'({NUMBER})(?:\s*/\s*({NUMBER}))?', text)
    if not parts:
        raise FormatError('Expected one numeric scalar, optionally a fraction')
    try:
        a = Fraction(Decimal(parts[1].replace(',', '')))
        result = a if parts[2] is None else a / Fraction(Decimal(parts[2].replace(',', '')))
    except (InvalidOperation, ZeroDivisionError) as e:
        raise FormatError(str(e)) from e
    return bounded(result)


def bounded(x):
    if abs(x) > 10**30 or x.numerator.bit_length() > 256 or x.denominator.bit_length() > 256:
        raise ResourceError('Numeric magnitude/precision limit')
    return x


def answer_field(text):
    lines = text.strip().splitlines()
    matches = [i for i, line in enumerate(lines) if line.startswith('FINAL:')]
    if len(matches) != 1 or matches[0] != len(lines) - 1:
        raise FormatError('Exactly one FINAL: field on the last line required')
    return numeric(lines[-1][6:])


def code_output(text):
    if len(text.strip().splitlines()) != 1:
        raise FormatError('Code must print exactly one FINAL: line')
    return answer_field(text)


def extract_code(text):
    text = text.strip()
    # Optional single whole-response fence; never find arbitrary embedded code.
    if text.startswith('```'):
        match = re.fullmatch(r'```(?:python)?\n(.*?)\n```', text, re.S)
        if not match:
            raise FormatError('Expected one complete Python code block')
        text = match[1]
    if not text or len(text.encode()) > 60000:
        raise FormatError('Empty/oversized code')
    ast.parse(text)
    return text


def arithmetic(text):
    """+ - * / // % **, unary +/-; decimal literals; exact rational arithmetic."""
    if len(text) > 1024:
        raise ResourceError('Expression length limit')
    try:
        tree = ast.parse(text.strip(), mode='eval')
    except (SyntaxError, ValueError) as e:
        raise FormatError(str(e)) from e
    if sum(1 for _ in ast.walk(tree)) > 128:
        raise ResourceError('AST node limit')

    def visit(n, depth=0):
        if depth > 32:
            raise ResourceError('Expression depth limit')
        if isinstance(n, ast.Constant) and type(n.value) in (int, float):
            token = ast.get_source_segment(text.strip(), n)
            # Reject Python alternate bases, underscore notation and scientific notation.
            return numeric(token)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            a = visit(n.operand, depth + 1)
            return a if isinstance(n.op, ast.UAdd) else -a
        if isinstance(n, ast.BinOp):
            a, b = visit(n.left, depth + 1), visit(n.right, depth + 1)
            if isinstance(n.op, ast.Add): result = a + b
            elif isinstance(n.op, ast.Sub): result = a - b
            elif isinstance(n.op, ast.Mult): result = a * b
            elif isinstance(n.op, ast.Div): result = a / b
            elif isinstance(n.op, ast.FloorDiv): result = Fraction(a // b)
            elif isinstance(n.op, ast.Mod): result = a % b
            elif isinstance(n.op, ast.Pow):
                if b.denominator != 1 or abs(b) > 12:
                    raise ResourceError('Integer exponent must be between -12 and 12')
                result = a ** int(b)
            else: raise FormatError('Operator not permitted')
            return bounded(result)
        raise FormatError('Only numeric literals and arithmetic operators permitted')
    return visit(tree.body)
