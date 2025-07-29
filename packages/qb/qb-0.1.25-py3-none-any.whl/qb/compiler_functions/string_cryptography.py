import re as regex

from hashlib import md5
from multiprocessing.pool import Pool
from typing import Any


def __encrypt_fstring(fstring: str) -> list[tuple[str, str | Any]]:
    fstring_content = fstring[1:]
    parts = regex.split(r"{.*}", fstring_content)
    encrypted_parts = []

    for part in parts:
        if part.strip() == "":
            continue

        part_id = "__string" + md5(part.encode()).hexdigest()

        encrypted_parts.append((part_id, part))

    return encrypted_parts

def __encrypt_string(string: str) -> list[tuple[str, str]]:
    string_id = "__string" + md5(string.encode()).hexdigest()

    return [(string_id, string)]


def encrypt_strings(code: str) -> tuple[str, list[tuple[str, str]]]:
    """Encrypts strings in code"""

    # find all strings
    strings = regex.findall(r"(?<!f)[\"'].*[\"']", code)
    fstrings = regex.findall(r"f[\"'].*[\"']", code)

    encrypted: list[tuple[str, str]] = []

    with Pool() as pool:
        encrypted_fstrings = pool.map(__encrypt_fstring, fstrings)
        encrypted_strings = pool.map(__encrypt_string, strings)

    # flatten list of lists
    encrypted += [item for sublist in encrypted_fstrings for item in sublist]
    encrypted += [item for sublist in encrypted_strings for item in sublist]

    for id_, content in encrypted:
        code = code.replace(content, id_)

    return code, encrypted


def decrypt_strings(code: str, encrypted_strings: list[tuple[str, str]]) -> str:
    """Decrypts strings in code"""

    for string_id, original_string in encrypted_strings:
        code = code.replace(string_id, original_string)

    return code
