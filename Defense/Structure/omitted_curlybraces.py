import glob

from lxml import etree


def init_parse(file):
    global doc
    doc = etree.parse(file)
    e = etree.XPathEvaluator(doc, namespaces={'src': 'http://www.srcML.org/srcML/src'})
    return e


def remove_unnecessary_braces(root):
    for tag in ['if', 'while', 'for']:
        for element in root.findall('.//src:' + tag, namespaces={'src': 'http://www.srcML.org/srcML/src'}):
            then = element.find('.//src:then', namespaces={'src': 'http://www.srcML.org/srcML/src'})
            if then is not None:
                block = then.find('.//src:block', namespaces={'src': 'http://www.srcML.org/srcML/src'})
                if block is not None and len(block.getchildren()) == 1 and block[0].tag == '{http://www.srcML.org/srcML/src}expr_stmt':
                    then.replace(block, block[0])
    return root


def save_tree_to_file(tree, file):
    with open(file, 'w') as f:
        f.write(etree.tostring(tree).decode('utf8'))

def program_transform(input_xml_path,prefix):
    tmp_xml = prefix+"tmp1.xml"
    e = init_parse(input_xml_path)
    tree_root = e('/*')[0].getroottree()
    tree_root = remove_unnecessary_braces(tree_root)
    save_tree_to_file(tree_root, tmp_xml)
    return tmp_xml