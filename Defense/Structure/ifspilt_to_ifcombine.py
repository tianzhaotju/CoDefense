import os
from glob import glob

from lxml import etree
from lxml.etree import Element

# 把if(a){if(b)}改为if(a&&b)
ns = {'src': 'http://www.srcML.org/srcML/src'}
doc = None
flag = True
str = '{http://www.srcML.org/srcML/src}'


def init_parse(file):
    global doc
    doc = etree.parse(file)
    e = etree.XPathEvaluator(doc, namespaces={'src': 'http://www.srcML.org/srcML/src'})
    return e


def get_if_stmt(e):
    return e('//src:if_stmt')


def get_secondIf(elem):
    return elem.xpath('src:if/src:block/src:block_content/src:if_stmt', namespaces=ns)


def get_condition2(elem):
    return elem.xpath('src:if/src:condition/src:expr', namespaces=ns)


def get_condition1(elem):
    return elem.xpath('src:if/src:condition/src:expr', namespaces=ns)


def get_content(elem):
    return elem.xpath('src:if/src:block/src:block_content', namespaces=ns)


def get_block(elem):
    return elem.xpath('src:if/src:block/src:block_content', namespaces=ns)


def save_tree_to_file(tree, file):
    with open(file, 'w') as f:
        f.write(etree.tostring(tree).decode('utf8'))


def trans_tree(e, ignore_list=[], instances=None):
    global flag
    flag = False
    tree_root = e('/*')[0].getroottree()
    new_ignore_list = []
    if_stmts = [get_if_stmt(e) if instances is None else (instance[0] for instance in instances)]
    for item in if_stmts:
        for if_stmt in item:

            if_stmt_prev = if_stmt.getprevious()
            if_stmt_prev = if_stmt_prev if if_stmt_prev is not None else if_stmt
            if_stmt_prev_path = tree_root.getpath(if_stmt_prev)
            if if_stmt_prev_path in ignore_list:
                continue

            if len(get_block(if_stmt)) > 0:
                block = get_block(if_stmt)[0]
                if len(block.getchildren()) == 1 and block.getchildren()[0].tag == str + 'if_stmt':
                    if_second = block.getchildren()[0]
                    if len(if_second) == 1 and if_second[0].text.strip() == 'if':
                        If2_condition = get_condition2(if_second)[0]
                        If1_condition = get_condition1(if_stmt)[0]
                        condition_flag = True
                        for expr_e in If2_condition:
                            if expr_e.text == '||' or expr_e.text == '|':
                                condition_flag = False
                        for expr_e in If1_condition:
                            if expr_e.text == '||' or expr_e.text == '|':
                                condition_flag = False
                        if condition_flag == False:
                            break
                        new_ignore_list.append(if_stmt_prev_path)
                        content = get_content(if_second)[0]
                        content.tail = ''
                        If1_condition.tail = ''
                        opreater = Element('operator')
                        opreater.text = '&&'
                        If1_condition.append(opreater)
                        If1_condition.append(If2_condition)
                        block.append(content)
                        block.remove(if_second)
                        flag = True
    return flag, tree_root, new_ignore_list


def count(e):
    count_num = 0
    if_second = None
    if_stmts = get_if_stmt(e)
    for if_stmt in if_stmts:
        if len(get_block(if_stmt)) > 0:
            block = get_block(if_stmt)[0]
            if len(block.getchildren()) == 1 and block.getchildren()[0].tag == str + 'if_stmt':
                if_second = block.getchildren()[0]
                if len(if_second) == 1 and if_second[0].text.strip() == 'if':
                    If2_condition = get_condition2(if_second)[0]
                    If1_condition = get_condition1(if_stmt)[0]
                    condition_flag = True
                    for expr_e in If2_condition:
                        if expr_e.text == '||' or expr_e.text == '|':
                            condition_flag = False
                    for expr_e in If1_condition:
                        if expr_e.text == '||' or expr_e.text == '|':
                            condition_flag = False
                    if condition_flag is False:
                        break
                    count_num += 1
    return count_num


# calculate the number of if
def get_number(xml_path):
    xml_file_path = os.path.abspath(xml_path)
    e = init_parse(xml_file_path)
    return count(e)


def program_transform(input_xml_path,prefix):
    tmp_xml = prefix+"tmp2.xml"
    e = init_parse(input_xml_path)
    flag, transformed_tree, ignore_list = trans_tree(e)
    save_tree_to_file(transformed_tree, tmp_xml)
    return tmp_xml
