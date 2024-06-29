import re


def remove_dead_code(code):
    code = re.sub(r';+', ';', code)
    code = re.sub(r'^\s*;\s*$', '', code, flags=re.MULTILINE)
    return code
