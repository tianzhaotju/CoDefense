import re


def remove_dead_code(java_code):
    pattern = r'System\.out\.(print|println)\(\s*("[^"{}]*"|\d+)?\s*\);'
    modified_code = re.sub(pattern, '', java_code)

    return modified_code
