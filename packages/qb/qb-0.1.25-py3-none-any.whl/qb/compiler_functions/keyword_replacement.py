import re as regex

from multiprocessing.pool import ThreadPool

definition_regex = regex.compile(r"\b(fn)\s+(\w+\s*\()")
lambda_regex = regex.compile(r"fn\s*([^->]*)->")
up_one_regex = regex.compile(r"(\w+)\s?\+\+")
down_one_regex = regex.compile(r"(\w+)\s?--")
not_equal_regex = regex.compile(r"<>")

range_function_regex_two_groups = regex.compile(r"(\w+)\.\.(\w+)")
range_function_regex_one_group = regex.compile(r"\.\.(\w+)")
range_function_regex_infinite = regex.compile(r"(\w+)\.\.")

entry_point_regex = regex.compile(r"@entrypoint(\(.*\))?\s+")


def __get_keyword_replacement_pair(r, code):
    re = r[0]
    sub = r[1]

    pairs = []
    matches = list(regex.finditer(re, code))

    for match in matches:
        _0 = match.group(0)
        _1 = regex.sub(re, sub, _0)

        pairs.append((_0, _1))

    return pairs

def replace_keywords(code):
    rules = [
        (definition_regex, r"def \2"),
        (lambda_regex, r"lambda \1:"),
        (up_one_regex, r"\1 += 1"),
        (down_one_regex, r"\1 -= 1"),
        (not_equal_regex, r"!=")
    ]

    with ThreadPool() as pool:
        found = pool.starmap(__get_keyword_replacement_pair, [(r, code) for r in rules])

    found = [item for sublist in found for item in sublist]

    for pair in found:
        code = code.replace(pair[0], pair[1])

    return code


def better_range(code):
    token = ".."

    if token not in code:
        return code

    for b in regex.findall(range_function_regex_two_groups, code):
        code = code.replace(f"{b[0]}{token}{b[1]}", f"range({b[0]}, {b[1]})")

    for b in regex.findall(range_function_regex_one_group, code):
        code = code.replace(f"{token}{b}", f"range({b})")

    for b in regex.findall(range_function_regex_infinite, code):
        code = code.replace(f"{b}{token}", f"infinite_range({b})")

    return code


def entry_point(code):
    entry_points = list(regex.finditer(entry_point_regex, code))

    if len(entry_points) == 0:
        return code

    if len(entry_points) > 1:
        raise Exception("Multiple entry points found")

    entry_point_found = entry_points[0]
    args = entry_point_found.group(1)

    if args is None:
        args = "()"

    next_line = ""
    for c in code[entry_point_found.end():]:
        if c == "\n":
            break

        next_line += c

    signature = list(regex.finditer(definition_regex, next_line))

    if len(signature) == 0:
        raise Exception("No function signature found after entry point")

    function_name = signature[0].group(2)[:-1]

    # quick and dirty fix
    poetry___name__ = "qb.__main__"

    idiom = f"\nif __name__ == \"{poetry___name__}\":\n\t{function_name}{args}"

    code += idiom
    code = code.replace("@entrypoint", "")

    return code
