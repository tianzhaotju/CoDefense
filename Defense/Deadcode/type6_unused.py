import re


def remove_dead_code(java_code):
    var_decl_pattern = r"\b([a-zA-Z_][a-zA-Z0-9_]*\s+[a-zA-Z_][a-zA-Z0-9_]*)\s*;"
    declarations = re.findall(var_decl_pattern, java_code)

    usage = {decl: False for decl in declarations}

    for decl in declarations:
        var_name = decl.split()[-1]
        if re.search(r"\b{}\b".format(var_name), java_code.replace(decl, "")):
            usage[decl] = True

    for decl, used in usage.items():
        if not used:
            java_code = java_code.replace(decl + ";", "")

    return java_code
