import re


def evaluate_expression(expression):
    try:
        return str(eval(expression))
    except Exception as e:
        return None


def remove_dead_code(source_code):
    source_code = re.sub(r'if\s*\(?\s*false\s*\)?\s*(?:\{\s*.*?\s*\})?\s*(?:else\s*\{\s*\})?\s*;\s*', '', source_code)
    source_code = re.sub(r'if\s*\(?\s*true\s*\)?\s*\{\s*(.*?)\s*\}\s*(?:else\s*\{\s*\}\s*)?;', r'\1', source_code)
    source_code = re.sub(r'if\s*\(?\s*0\s*\)?\s*(?:\{\s*.*?\s*\})?\s*(?:else\s*\{\s*\})?\s*;\s*', '', source_code)
    source_code = re.sub(r'if\s*\(?\s*[1-9][0-9]*\s*\)?\s*\{\s*(.*?)\s*\}\s*(?:else\s*\{\s*\}\s*)?;', r'\1',
                         source_code)

    expressions = re.findall(r'if\s*\(?\s*([^()]*)\s*\)?\s*\{', source_code)
    for exp in expressions:
        # 判断条件是否为恒等式（例如a==a、a!=a）
        if '==' in exp or '!=' in exp:
            if len(set(re.findall(r'\b\w+\b', exp))) == 1:
                value = 'True' if '==' in exp else 'False'
            else:
                value = evaluate_expression(exp)

            if value == "True":
                source_code = re.sub(
                    f'if\s*\(?\s*{re.escape(exp)}\s*\)?\s*\{{\s*(.*?)\s*\}}\s*(?:else\s*\{{\s*\}}\s*)?;', r'\1',
                    source_code)
            else:
                source_code = re.sub(
                    f'if\s*\(?\s*{re.escape(exp)}\s*\)?\s*\{{\s*.*?\s*\}}\s*(?:else\s*\{{\s*\}}\s*)?;', '',
                    source_code)

    return source_code
