import sys

sys.dont_write_bytecode = True

import shutil
import os

from pathlib import Path

from .compiler_functions import manage_pipes
from .compiler_functions import encrypt_strings, decrypt_strings
from .compiler_functions import preprocess
from .compiler_functions import better_range, replace_keywords, entry_point
from .compiler_functions import multi_line_lambda
from .compiler_functions import transform_lists

from qb_runtime import *

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    if len(args) == 0:
        print("No file specified.")
        return

    file = args[0]

    if not file.endswith(".qb"):
        print("File must be a .qb file")
        return

    path = os.path.abspath(file)

    if not os.path.exists(path):
        print("File not found")
        return

    marked_for_deletion = []

    try:
        code = compile_to_qb(path)

        dirname = os.path.dirname(path)
        sys.path = [dirname] + sys.path

        for lib_path in Path(dirname).rglob("*.qb"):
            lib_path = str(lib_path)

            if lib_path == path:
                continue

            lib_code = compile_to_qb(lib_path)

            lib_path = lib_path.replace(".qb", ".py")
            write(lib_path, lib_code)

            marked_for_deletion.append(lib_path)

        # Get code ready to be executed
        sys.setrecursionlimit(2**31 - 1)
        sys.argv = [path] + args[1:]

        exec(code, globals())

        for file in marked_for_deletion:
            os.remove(file)

        pycache = os.path.join(dirname, "__pycache__")
        if os.path.exists(pycache):
            shutil.rmtree(pycache)

    except Exception as e:
        for file in marked_for_deletion:
            os.remove(file)

        dirname = os.path.dirname(path)

        pycache = os.path.join(dirname, "__pycache__")
        if os.path.exists(pycache):
            shutil.rmtree(pycache)

        raise e


def read(path):
    with open(path, "r") as file:
        return file.read()


def write(path, content):
    with open(path, "w") as file:
        file.write(content)


def compile_to_qb(path):
    code = read(path)

    encrypted = encrypt_strings(code)

    code = encrypted[0]
    encrypted_strings = encrypted[1]

    code = preprocess(code)
    code = multi_line_lambda(code)
    code = entry_point(code)
    code = replace_keywords(code)
    code = better_range(code)
    code = transform_lists(code)
    code = manage_pipes(code)

    code = decrypt_strings(code, encrypted_strings)

    return code


# if __name__ == "__main__":
#     main(sys.argv[1:])
#
#
# else:
#     print(
#         """⠁⡼⠋⠀⣆⠀⠀⣰⣿⣫⣾⢿⣿⣿⠍⢠⠠⠀⠀⢀⠰⢾⣺⣻⣿⣿⣿⣷⡀⠀
# ⣥⠀⠀⠀⠁⠀⠠⢻⢬⠁⣠⣾⠛⠁⠀⠀⠀⠀⠀⠀⠀⠐⠱⠏⡉⠙⣿⣿⡇⠀
# ⢳⠀⢰⡖⠀⠀⠈⠀⣺⢰⣿⢻⣾⣶⣿⣿⣶⣶⣤⣤⣴⣾⣿⣷⣼⡆⢸⣿⣧⠀
# ⠈⠀⠜⠈⣀⣔⣦⢨⣿⣿⣿⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣅⣼⠛⢹⠀
# ⠀⠀⠀⠀⢋⡿⡿⣯⣭⡟⣟⣿⣿⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⡘⠀
# ⡀⠐⠀⠀⠀⣿⣯⡿⣿⣿⣿⣯⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠋⣉⢽⣿⡆⠀⠀
# ⢳⠀⠄⠀⢀⣿⣿⣿⣿⣿⣿⣿⠙⠉⠉⠉⠛⣻⢛⣿⠛⠃⠀⠐⠛⠻⣿⡇⠀⠀
# ⣾⠄⠀⠀⢸⣿⣿⡿⠟⠛⠁⢀⠀⢀⡄⣀⣠⣾⣿⣿⡠⣴⣎⣀⣠⣠⣿⡇⠀⠀
# ⣧⠀⣴⣄⣽⣿⣿⣿⣶⣶⣖⣶⣬⣾⣿⣾⣿⣿⣿⣿⣽⣿⣿⣿⣿⣿⣿⡇⠀⠀
# ⣿⣶⣈⡯⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠋⣹⢧⣿⣿⣿⣄⠙⢿⣿⣿⣿⠇⠀⠀
# ⠹⣿⣿⣧⢌⢽⣻⢿⣯⣿⣿⣿⣿⠟⣠⡘⠿⠟⠛⠛⠟⠛⣧⡈⠻⣾⣿⠀⠀⠀
# ⠀⠈⠉⣷⡿⣽⠶⡾⢿⣿⣿⣿⢃⣤⣿⣷⣤⣤⣄⣄⣠⣼⡿⢷⢀⣿⡏⠀⠀⠀
# ⠀⠀⢀⣿⣷⠌⣈⣏⣝⠽⡿⣷⣾⣏⣀⣉⣉⣀⣀⣀⣠⣠⣄⡸⣾⣿⠃⠀⠀⠀
# ⠀⣰⡿⣿⣧⡐⠄⠱⣿⣺⣽⢟⣿⣿⢿⣿⣍⠉⢀⣀⣐⣼⣯⡗⠟⡏⠀⠀⠀⠀
# ⣰⣿⠀⣿⣿⣴⡀⠂⠘⢹⣭⡂⡚⠿⢿⣿⣿⣿⡿⢿⢿⡿⠿⢁⣴⣿⣷⣶⣦⣤
#
#     Are you aight, mate?
# """
#     )
