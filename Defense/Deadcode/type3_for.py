import re


def remove_dead_code(source_code):
    for_loops = re.findall(r'(for\s*\([^)]*\)\s*\{)([^}]*)\}', source_code)

    for loop_header, body in for_loops:
        statements = [stmt.strip() for stmt in body.split(';')]
        if statements[0] == "break":
            full_loop = re.escape(loop_header) + re.escape(body) + r'\}'
            source_code = re.sub(full_loop, '', source_code, count=1)

    return source_code
