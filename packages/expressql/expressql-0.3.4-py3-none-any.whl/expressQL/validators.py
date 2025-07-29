import re

def is_number(s):
    """
    Check if the string s can be converted to a float.
    This is a simple check and does not cover all edge cases.
    """
    try:
        float(s)
        return True
    except ValueError:
        return False
    except TypeError:
        return False



def validate_subquery_safe(where: str) -> None:
    """
    Validates that the provided SQL subquery string is safe and adheres to specific rules.
    This function ensures that the subquery:
    - Is not empty.
    - Contains only a single SQL statement.
    - Starts with a SELECT statement.
    - Does not contain semicolons within the query (except at the very end, if present).
    Parameters:
        where (str): The SQL subquery string to validate.
    Raises:
        ValueError: If the subquery is empty, contains multiple statements, 
                    does not start with a SELECT statement, or contains invalid semicolons.
    """
    
    import sqlparse
    from sqlparse.sql import Identifier, IdentifierList
    from sqlparse.tokens import DML
    parsed = sqlparse.parse(where)
    if not parsed:
        raise ValueError("Empty subquery is not allowed.")

    stmt = parsed[0]  # Assume one statement
    first_token = stmt.token_first(skip_cm=True)

    if not first_token:
        raise ValueError("Subquery must have content.")
    
    if first_token.ttype != DML or first_token.value.upper() != 'SELECT':
        raise ValueError("Only SELECT subqueries are allowed.")

    if len(parsed) > 1:
        raise ValueError("Multiple statements are not allowed in subquery.")

    if ";" in where[:-1]:  # extra paranoia
        raise ValueError("Semicolons are not allowed inside the subquery.")

    # You could do even *deeper* validation, but this is already good for now.

def get_forbidden_words_in(name: str):
    """
    Identifies SQL keywords present in the given string.
    This function checks if any SQL reserved keywords are present in the 
    provided string `name`. It performs a case-insensitive search and 
    returns a list of all matching keywords.
    Args:
        name (str): The input string to be checked for SQL keywords.
    Returns:
        list: A list of SQL keywords found in the input string. If no 
        keywords are found, an empty list is returned.
    Example:
        >>> get_forbidden_words_in("SELECT name FROM users")
        ['SELECT', 'FROM']
    """

    keywords = {
        "SELECT", "FROM", "WHERE", "TABLE", "INSERT", "UPDATE", "DELETE",
        "CREATE", "DROP", "ALTER", "JOIN", "ON", "AS", "AND", "OR", "NOT",
        "IN", "IS", "NULL", "VALUES", "SET", "GROUP", "BY", "ORDER", "HAVING",
        "LIMIT", "OFFSET", "DISTINCT"
    }
    found = []
    for keyword in keywords:
        if re.search(rf'\b{keyword}\b', name, flags=re.IGNORECASE):
            found.append(keyword)
    return found
        
def validate_name_regex(

    name: str, *, 
    validate_words: bool = True,
    validate_len: bool = True,
    allow_dot: bool = False
) -> None:
    """
    Validates a column name based on specific rules and constraints.
    Args:
        name (str): The column name to validate.
        validate_words (bool, optional): If True, checks for forbidden words in the name. Defaults to True.
        validate_len (bool, optional): If True, ensures the name does not exceed 255 characters. Defaults to True.
        allow_dot (bool, optional): If True, allows dots (.) in the column name. Defaults to False.
    Raises:
        TypeError: If the provided name is not a string.
        ValueError: If the name is a number, empty, too long, contains invalid characters, 
                    or includes forbidden words (when `validate_words` is True).
    """
    if not isinstance(name, str):
        raise TypeError("Column name must be a string.")

    if is_number(name):
        raise ValueError("Column name cannot be a number.")

    if len(name) == 0:
        raise ValueError("Column name cannot be empty.")

    if validate_len and len(name) > 255:
        raise ValueError("Column name is too long. Maximum length is 255 characters.")

    if allow_dot:
        pattern = r'^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$'
    else:
        pattern = r'^[A-Za-z_][A-Za-z0-9_]*$'

    if not re.match(pattern, name):
        raise ValueError(f"Column name {name} is invalid.")

    if validate_words:
        found = get_forbidden_words_in(name)
        if found:
            raise ValueError(f"Column name contains forbidden words: {found}")

keywords = {
        "select", "from", "where", "table", "insert", "update", "delete",
        "create", "drop", "alter", "join", "on", "as", "and", "or", "not",
        "in", "is", "null", "values", "set", "group", "by", "order", "having",
        "limit", "offset", "distinct"
    }



def get_forbidden_words_in(name: str):

    tokens = name.casefold().replace('.', ' ').replace('_', ' ').split()
    return [kw for kw in keywords if kw in tokens]

def validate_name(
    name: str, *, 
    validate_chars: bool = True, 
    validate_words: bool = True, 
    validate_len: bool = True,
    allow_dot: bool = True,
    allow_dollar: bool = False,
    max_len: int = 255,
    forgiven_chars = set(),
    allow_digit: bool = False,
) -> None:
    


    if not isinstance(name, str):
        raise TypeError("Name must be a string.")

    if is_number(name):
        raise ValueError("Column name cannot be a number.")

    if len(name) == 0:
        raise ValueError("Column name cannot be empty.")

    if validate_len and len(name) > max_len:
        raise ValueError("Column name is too long. Maximum length is 255 characters.")

    if name[0].isdigit() and not allow_digit:
        raise ValueError("Column name cannot start with a digit.")
    
    



    if validate_chars:
        # Base set of allowed non-alphanumeric characters
        allowed = set(forgiven_chars) | set('_')
        if allow_dot:
            allowed.add('.')
        if allow_dollar:
            allowed.add('$')

        # Check characters one by one
        bad_chars = [
            c for c in name
            if not (c.isalnum() or c in allowed)
        ]
        if bad_chars:
            raise ValueError(f"Column name contains forbidden characters: {bad_chars}")

        if allow_dot:
            # Ensure valid dot-separated parts
            parts = name.split('.')
            for part in parts:
                if not part:
                    raise ValueError("Column name has consecutive dots or leading/trailing dot.")
                if part[0].isdigit():
                    raise ValueError(f"Each part of a dotted name must not start with a digit: {part}")


    if validate_words:
        found = next((word for word in keywords if word == name.casefold()), None)
        if found:
            raise ValueError(f"Name contains forbidden words: {found}")
