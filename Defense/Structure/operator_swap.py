from lxml import etree
import glob

def init_parse(file):
    global doc
    doc = etree.parse(file)
    e = etree.XPathEvaluator(doc, namespaces={'src': 'http://www.srcML.org/srcML/src'})
    return e

def random_swap_operands(e):
    operators = ['<', '>', '<=', '>=', '==', '!=', '&&', '||', '+', '*']
    opposite_operators = {'<': '>', '>': '<', '<=': '>=', '>=': '<='}

    for op in operators:
        exprs = e.xpath(f"//src:expr[src:operator='{op}' and not(@swapped='true')]",
                        namespaces={'src': 'http://www.srcML.org/srcML/src'})
        for expr in exprs:
            operands = expr.xpath('./src:expr', namespaces={'src': 'http://www.srcML.org/srcML/src'})
            if len(operands) == 2:
                parent = operands[0].getparent()
                parent.replace(operands[0], operands[1])
                parent.replace(operands[1], operands[0])

                if op in opposite_operators:
                    expr.find('.//src:operator', namespaces={'src': 'http://www.srcML.org/srcML/src'}).text = \
                        opposite_operators[op]

                expr.set('swapped', 'true')

    return e

def save_tree_to_file(tree, file):
    with open(file, 'w') as f:
        f.write(etree.tostring(tree).decode('utf8'))

def program_transform(input_xml_path,prefix):
    tmp_xml = prefix+"tmp1.xml"
    e = init_parse(input_xml_path)
    tree_root = e('/*')[0].getroottree()
    tree_root = random_swap_operands(tree_root)
    save_tree_to_file(tree_root, tmp_xml)
    return tmp_xml
