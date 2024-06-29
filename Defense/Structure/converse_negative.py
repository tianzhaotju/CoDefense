from lxml import etree
import glob


def init_parse(file):
    global doc
    doc = etree.parse(file)
    e = etree.XPathEvaluator(doc, namespaces={'src': 'http://www.srcML.org/srcML/src'})
    return e


def negate_expression(expr):
    negation_map = {
        '>': '<=',
        '<': '>=',
        '==': '!=',
        '!=': '==',
        '&&': '||',
        '||': '&&'
    }

    operator_element = expr.find('.//src:operator', namespaces={'src': 'http://www.srcML.org/srcML/src'})
    if operator_element is not None:
        operator = operator_element.text
        if operator in negation_map:
            operator_element.text = negation_map[operator]
            parent = expr.getparent()
            not_expr = etree.Element("{http://www.srcML.org/srcML/src}expr")
            not_expr.text = '!'
            not_expr.append(expr)
            parent.append(not_expr)


def process_conditionals(e):
    conditionals = e.xpath("//src:if//src:condition", namespaces={'src': 'http://www.srcML.org/srcML/src'})
    for conditional in conditionals:
        expressions = conditional.xpath('.//src:expr', namespaces={'src': 'http://www.srcML.org/srcML/src'})
        for expr in expressions:
            negate_expression(expr)
    return e


def save_tree_to_file(tree, file):
    with open(file, 'w') as f:
        f.write(etree.tostring(tree).decode('utf8'))


def program_transform(input_xml_path,prefix):
    tmp_xml = prefix+"tmp1.xml"
    e = init_parse(input_xml_path)
    tree_root = e('/*')[0].getroottree()
    tree_root = process_conditionals(tree_root)
    save_tree_to_file(tree_root, tmp_xml)
    return tmp_xml
