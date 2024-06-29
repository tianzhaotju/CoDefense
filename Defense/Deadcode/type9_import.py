import re

def remove_dead_code(code):
    lines = code.split('\n')
    used_imports = []
    unused_import_indices = []

    # 找到所有的import语句并检查是否被使用
    for index, line in enumerate(lines):
        if 'import' in line:
            # 使用正则表达式提取完整的包名和类名
            match = re.search(r'import\s+([\w\.]+);', line)
            if match:
                full_import = match.group(1)
                class_name = full_import.split('.')[-1]  # 获取类名
                # 检查是否在后续代码中使用了这个类名
                if any(re.search(r'\b' + re.escape(class_name) + r'\b', line) for line in lines[index + 1:]):
                    used_imports.append(line)
                else:
                    unused_import_indices.append(index)

    # 删除未使用的import语句
    for index in sorted(unused_import_indices, reverse=True):
        del lines[index]

    # 返回修改后的代码
    return '\n'.join(lines)
