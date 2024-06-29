from lxml import etree
import glob


def init_parse(file):
    doc = etree.parse(file)
    e = etree.XPathEvaluator(doc, namespaces={'src': 'http://www.srcML.org/srcML/src'})
    return e


def replace_type(e, old_type, new_type):
    # 找到所有指定的旧数据类型
    type_elements = e(f"//src:type[src:name='{old_type}']/src:name")
    for elem in type_elements:
        elem.text = new_type


def save_tree_to_file(doc, file):
    with open(file, 'wb') as f:
        f.write(etree.tostring(doc, pretty_print=True, xml_declaration=True, encoding='UTF-8'))


def program_transform(program_path,prefix):
    tmp_xml = prefix+"tmp1.xml"
    e = init_parse(program_path)
    # 进行数据类型转换
    replace_type(e, 'int', 'long')
    replace_type(e, 'char', 'String')
    replace_type(e, 'float', 'double')
    tree_root = e('/*')[0].getroottree()
    # 保存修改后的XML文件
    save_tree_to_file(tree_root, tmp_xml)
    return tmp_xml

