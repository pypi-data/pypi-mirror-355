import re as regex
import random
import time

from hashlib import md5

def multi_line_lambda(code):
    multiline_lambda_regex = r"fn\s+(.*)->\s*{\|([\S\s]*)\|}"
    match = regex.search(multiline_lambda_regex, code)

    # Wenn keine Übereinstimmung gefunden wird, geben wir den Code zurück
    if match is None:
        return code

    _vars = match.group(1)
    _code = match.group(2)

    function_name = "__lambda" + md5(match.group(0).encode()).hexdigest()

    body = "{|" + _code + "|}"

    definition = f"def {function_name}({_vars}):{_code}"
    call = f"{function_name}({_vars})"

    code = code.replace(body, call)

    index = match.start()
    code_to_search = code[:index][::-1]

    for c in code_to_search:
        if c == "\n":
            break

        index -= 1

    indent = ""
    for c in code[index:]:
        if c.strip() == "":
            indent += c

        else:
            break

    code = code[:index] + indent + definition + code[index + len(indent):]

    # Rufe die Funktion rekursiv auf, um weitere Übereinstimmungen zu finden
    return multi_line_lambda(code)