from warnings import warn
from multiprocessing.pool import ThreadPool


def preprocess(code):
    raise_errors_and_warnings(code)

    code = code.replace("|>", ">>")
    code = code.replace("<|", "<<")

    return code


def __raise_error(rule, code):
    problem = rule[0]
    exception = rule[1]

    if any([p in code for p in problem]):
        if isinstance(exception, SyntaxError):
            raise exception

        warn(exception)

def raise_errors_and_warnings(code):
    shifting_operators = ["<<", ">>"]
    shifting_error = SyntaxError("When bit shifting, use the 'lshift' and 'rshift' function instead of the '<<' and '>>' operators")

    io_functions = ["print", "input"]
    io_warning = SyntaxWarning("When performing io-operations, use cout and cin instead of the 'print' and 'input' functions respectively")

    function_definitions = ["def", "lambda"]
    function_error = SyntaxWarning(
        "When defining a function, use the 'fn' keyword instead of 'def' or 'lambda' like so: 'fn x -> x ** 2'"
    )

    not_operator = ["!="]
    not_error = SyntaxWarning("When checking for inequality, use the '<>' operator instead of '!='")

    rules = [
        (shifting_operators, shifting_error),
        (io_functions, io_warning),
        (function_definitions, function_error),
        (not_operator, not_error)
    ]

    with ThreadPool() as pool:
        pool.starmap(__raise_error, [(rule, code) for rule in rules])