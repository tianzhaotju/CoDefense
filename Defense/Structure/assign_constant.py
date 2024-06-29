import glob

from lxml import etree
import string
import random


def init_parse(file):
    global doc
    doc = etree.parse(file)
    e = etree.XPathEvaluator(doc, namespaces={'src': 'http://www.srcML.org/srcML/src'})
    return e


def generate_var_name(size=1):
    # 随机生成一个变量名
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(size))


def determine_literal_type(value):
    # 确定字面量的数据类型
    try:
        val = int(value)
        # 检查是否可能是long
        if val.bit_length() > 31:
            return "long"
        return "int"
    except ValueError:
        pass

    try:
        float(value)
        return "double"
    except ValueError:
        pass

    if value.startswith("'") and value.endswith("'") and len(value) == 3:
        return "char"

    return "string"


def process_assignments(e):
    # 查找所有赋值表达式
    assignments = e.xpath("//src:expr_stmt/src:expr", namespaces={'src': 'http://www.srcML.org/srcML/src'})
    for expr in assignments:
        # 查找常数和字符串
        literals = expr.xpath(".//src:literal", namespaces={'src': 'http://www.srcML.org/srcML/src'})
        if literals:
            literal = literals[0]  # 只处理第一个常数或字符串
            literal_value = literal.text.strip().strip('"').strip("'")
            literal_type = determine_literal_type(literal_value)
            new_var_name = generate_var_name()

            # 创建新的变量声明
            decl_stmt = etree.Element("{http://www.srcML.org/srcML/src}decl_stmt")
            decl = etree.SubElement(decl_stmt, "{http://www.srcML.org/srcML/src}decl")
            decl_type = etree.SubElement(decl, "{http://www.srcML.org/srcML/src}type")
            decl_type.text = literal_type
            decl_name = etree.SubElement(decl, "{http://www.srcML.org/srcML/src}name")
            decl_name.text = new_var_name
            decl_init = etree.SubElement(decl, "{http://www.srcML.org/srcML/src}init")
            decl_init.text = literal.text

            # 将新的变量声明插入到合适的位置
            parent_block = expr.getparent().getparent()  # 获取 expr_stmt 的父级元素，通常是 block
            parent_block.insert(0, decl_stmt)

            # 替换原始表达式中的常数或字符串
            literal.getparent().remove(literal)
            new_var = etree.Element("{http://www.srcML.org/srcML/src}name")
            new_var.text = new_var_name
            expr.append(new_var)
    return e


def save_tree_to_file(tree, file):
    with open(file, 'w') as f:
        f.write(etree.tostring(tree).decode('utf8'))


def program_transform(input_xml_path,prefix):
    tmp_xml = prefix+"tmp1.xml"
    e = init_parse(input_xml_path)
    tree_root = e('/*')[0].getroottree()
    tree_root = process_assignments(tree_root)
    save_tree_to_file(tree_root, tmp_xml)
    return tmp_xml
