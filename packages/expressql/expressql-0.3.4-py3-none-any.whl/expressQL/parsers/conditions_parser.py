from .expressions_parser import parse_expression, extract_replace_outermost_bracketed_withfunc
from .parsing_utils import (is_outer_bracketed,
     bracket_string_sandwich, extract_replace_outermost_bracketed,
     remove_outer_brackets)
import re
from ..base import (
    SQLCondition, SQLChainCondition,
    AndCondition, OrCondition, NotCondition, SubQuery
)
from .subquery_placeholder import parametrize_subquery
class _ConditionToken:
    pass

class ConditionToken(_ConditionToken):
    """
    Represents a token in a condition expression.
    This class is used to parse and represent conditions in SQL-like expressions.
    """
    def __init__(self, value: str):
        self.value = value

    def __repr__(self):
        return f"ConditionToken({self.value!r})"
    
    def _can_simple_resolve(self) -> bool:
        value = self.value.strip()
        check = not any(char in value.upper() for char in ("AND", "OR", "NOT", "BETWEEN", "LIKE", "IN", "IS", "EXISTS"))

    def resolve(self) -> SQLCondition:
        return parse_condition(self.value)



def split_top_level(s: str, sep: str) -> list[str]:
    """
    Split s on the literal sep (e.g. 'AND' or 'OR'), but only at depth==0.
    Returns the list of trimmed segments.
    """
    parts = []
    depth = 0
    last = 0
    i = 0
    L = len(sep)
    upper = s.upper()
    while i < len(s):
        c = s[i]
        if c == "(":
            depth += 1; i += 1
        elif c == ")":
            depth -= 1; i += 1
        # match sep at depth 0
        elif depth == 0 and upper[i : i + L] == sep:
            parts.append(s[last : i].strip())
            last = i + L
            i += L
        else:
            i += 1
    parts.append(s[last:].strip())
    return parts

def find_lhs_expression(s: str, between_idx: int) -> tuple[int, str]:
    """
    Given s and the index of the B in BETWEEN,
    return (lhs_start, lhs_expr), where lhs_expr is the
    full expression immediately to the left of BETWEEN,
    including any function-call parentheses.
    """
    j = between_idx - 1
    depth = 0
    extra = set("+-*/%")
    have_started = False

    while j >= 0:
        c = s[j]

        # 1) before we've started, just skip any leading spaces
        if not have_started:
            if c.isspace():
                j -= 1
                continue
            have_started = True

        # 2) closing paren always increases nesting
        if c == ')':
            depth += 1
            j -= 1
            continue

        # 3) opening paren always decreases nesting
        if c == '(':
            j -= 1
            depth -= 1
            # once depth < 0, that '(' belongs *outside* our expr → stop
            if depth < 0:
                break
            continue

        # 4) if we are inside ANY parentheses, consume *everything*
        if depth > 0:
            j -= 1
            continue

        # 5) at depth==0, only letters/digits/dot/underscore/operators are allowed
        if c.isalnum() or c in "._" or c in extra:
            j -= 1
            continue

        # 6) a top-level space or any other character is our hard stop
        break

    lhs_start = j + 1
    lhs_expr  = s[lhs_start:between_idx].strip()
    return lhs_start, lhs_expr



def find_top_level_and(s: str, start_idx: int) -> int:
    """
    From start_idx onwards, return the index of the first top‐level 'AND',
    or -1 if none.
    """
    depth = 0
    i = start_idx
    upper = s.upper()
    N = len(s)

    while i < N:
        c = s[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
        elif depth == 0 \
             and upper.startswith("AND", i) \
             and (i+3 == N or not (s[i+3].isalnum() or s[i+3] == "_")):
            return i
        i += 1

    return -1


def find_rhs_expression(s: str, and_pos: int) -> tuple[int, str]:
    """
    Given the index of the 'A' in the AND,
    return (end_hi, hi_expr), where end_hi is the first index
    after the high bound (just before the next AND/OR at depth 0 or end of s).
    """
    # skip over "AND"
    m = and_pos + len("AND")
    N = len(s)
    while m < N and s[m].isspace():
        m += 1

    depth = 0
    upper = s.upper()

    while m < N:
        c = s[m]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1

        if depth == 0:
            if upper.startswith("AND", m) and (m+3 == N or not (s[m+3].isalnum() or s[m+3] == "_")):
                break
            if upper.startswith("OR", m) and (m+2 == N or not (s[m+2].isalnum() or s[m+2] == "_")):
                break

        m += 1

    hi_expr = s[and_pos + len("AND"):m].strip()
    return m, hi_expr

def transform_betweens(s: str) -> str:
    s_upper = s.upper()
    out = []
    i = 0
    N = len(s)

    while i < N:
        idx = s_upper.find("BETWEEN", i)
        if idx < 0:
            out.append(s[i:])
            break

        # 1) find LHS
        lhs_start, lhs = find_lhs_expression(s, idx)

        # 2) copy everything up to the LHS
        out.append(s[i:lhs_start])

        # 3) find the matching AND
        and_pos = find_top_level_and(s, idx + len("BETWEEN"))
        if and_pos < 0:
            raise ValueError(f"Invalid BETWEEN syntax (no AND): {s!r}")

        # 4/5) extract lo and hi bounds
        lo = s[idx + len("BETWEEN") : and_pos].strip()
        end_hi, hi = find_rhs_expression(s, and_pos)

        # 6) emit expanded form *with* a trailing space
        out.append(f"( {lhs} >= {lo} AND {lhs} <= {hi} ) ")

        # advance
        i = end_hi

    return "".join(out)

def parse_condition(s: str, *, outer_brackets_removed:bool = False) -> SQLCondition:

    s = s.strip()
    # 1) strip outer parentheses
    if not outer_brackets_removed:
        s = remove_outer_brackets(s)

    # 2) split top-level OR
    or_parts = split_top_level(s, "OR")
    if len(or_parts) > 1:
        return OrCondition(*[parse_condition(p) for p in or_parts])

    s = transform_betweens(s)
    # 3) split top-level AND

    and_parts = split_top_level(s, "AND")
    if len(and_parts) > 1:
        return AndCondition(*[parse_condition(p) for p in and_parts])



    # 4) handle NOT
    if s.upper().startswith("NOT "):
        return NotCondition(parse_condition(s[4:].strip()))

    # 5) Handle IN
    if "NOT IN " in s.upper():
        # split on NOT IN, preserving the NOT IN keyword
        tokens = re.split(r"\s*NOT\s+IN\s*", s, maxsplit=1)
        if len(tokens) != 2:
            raise ValueError(f"Invalid NOT IN condition: {s!r}")
        # parse the left side as an expression
        left_expr = parse_expression(tokens[0].strip())
        # parse the right side as a subquery or a list of values
        right_side = tokens[1].strip()
        pure_right_side = remove_outer_brackets(right_side)
        if pure_right_side.startswith("SELECT"):
            # it's a subquery
            subquery, placeholders = parametrize_subquery(pure_right_side, style="?")
            return left_expr.not_in_subquery(subquery, params=placeholders)
        else:
            right_expr = parse_expression(right_side)
            return left_expr.is_not_in(right_expr)
    elif " IN " in s.upper():
        # split on IN, preserving the IN keyword
        s = s.replace("in", "IN").replace("In", "IN").replace("iN", "IN")
        tokens = re.split(r"\s*IN\s*", s, maxsplit=1)

        if len(tokens) != 2:
            raise ValueError(f"Invalid IN condition: {s!r}")
        # parse the left side as an expression
        left_expr = parse_expression(tokens[0].strip())
        # parse the right side as a subquery or a list of values
        right_side = tokens[1].strip()
        pure_right_side = remove_outer_brackets(right_side)
        if remove_outer_brackets(right_side).upper().startswith("SELECT"):
            # it's a subquery
            subquery, placeholders = parametrize_subquery(pure_right_side, style="?")
            return left_expr.is_in_subquery(subquery, params=placeholders)
        else:
            right_expr = parse_expression(right_side)
            return left_expr.is_in(right_expr)
        

    if " IS NULL" in s.upper():
        # split on IS NULL, preserving the IS NULL keyword
        tokens = re.split(r"\s*IS\s+NULL\s*", s, maxsplit=1)
        if len(tokens) != 2:
            raise ValueError(f"Invalid IS NULL condition: {s!r}")
        # parse the left side as an expression
        left_expr = parse_expression(tokens[0].strip())
        return left_expr.is_null()
    elif " IS NOT NULL" in s.upper():
        # split on IS NOT NULL, preserving the IS NOT NULL keyword
        tokens = re.split(r"\s*IS\s+NOT\s+NULL\s*", s, maxsplit=1)
        if len(tokens) != 2:
            raise ValueError(f"Invalid IS NOT NULL condition: {s!r}")
        # parse the left side as an expression
        left_expr = parse_expression(tokens[0].strip())
        return left_expr.is_not_null()


    
    # 6) finally, comparators / chain
    #    split on comparators, preserving them in the list:
    tokens = re.split(r"\s*(<=|>=|!=|=|<|>)\s*", s)

    if len(tokens) >= 3:
        # e.g. ['a', '<', 'b', '<', 'c + d']
        items: list[object] = []
        for i, tok in enumerate(tokens):
            if i % 2 == 0:
                # operand: parse as an expression

                items.append(parse_expression(tok))
            else:
                # comparator: keep as string

                items.append(tok)

        # build a chained condition
        return SQLChainCondition(*items)

    # if we fall through, it's not a valid condition string
    raise ValueError(f"Can't parse condition: {s!r}")




