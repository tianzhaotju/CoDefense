import re


def evaluate_expression(expression):
    try:
        return str(eval(expression))
    except Exception as e:
        return None


def remove_dead_code(source_code):
    while_statements = re.findall(r'while\s*\(?\s*([^()]*)\s*\)?\s*\{(.*?)\}', source_code, re.DOTALL)
    for exp, body in while_statements:
        if "break;" in body.strip().split("\n")[0]:
            source_code = re.sub(
                f'while\s*\(?\s*{re.escape(exp)}\s*\)?\s*{{\s*{re.escape(body)}\s*}}\s*;', '', source_code,
                flags=re.DOTALL)
        else:
            source_code = re.sub(r'while\s*\(?\s*false\s*\)?\s*(?:\{\s*.*?\s*\})?\s*;\s*', '', source_code)
            source_code = re.sub(r'while\s*\(?\s*0\s*\)?\s*(?:\{\s*.*?\s*\})?\s*;\s*', '', source_code)

            if len(set(re.findall(r'\b\w+\b', exp))) == 1:
                if '==' in exp:
                    value = 'True'
                elif '!=' in exp:
                    value = 'False'
                else:
                    value = 'None'
            else:
                value = evaluate_expression(exp)

            if value == "False":
                source_code = re.sub(f'while\s*\(?\s*{re.escape(exp)}\s*\)?\s*{{\s*{re.escape(body)}\s*}}\s*;', '',
                                     source_code, flags=re.DOTALL)
            else:
                continue

    return source_code
