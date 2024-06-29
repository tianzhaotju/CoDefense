import re


def remove_dead_code(java_code):
    java_code = re.sub(r'assertTrue\s*\(\s*(true|True|\d+\s*[>\s*]+\s*0)\s*\)\s*;', '', java_code)

    java_code = re.sub(r'assertEqual\s*\(\s*(\w+)\s*,\s*\1\s*\)\s*;', '', java_code)

    return java_code
