import re


def remove_dead_code(code):
    pattern = re.compile(r'{\s*}')
    while re.search(pattern, code):
        code = re.sub(pattern, '', code)
    return code
