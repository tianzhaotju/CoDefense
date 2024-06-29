def program_transform(program_path, prefix):
    if not program_path.startswith(prefix):
        program_path = prefix + program_path
    tmp_xml = program_path.split('/')
    tmp_xml[-1] = 'copy_'+tmp_xml[-1]
    tmp_xml = '/'.join(tmp_xml)
    f = open(tmp_xml, 'w')
    f.write(open(program_path, 'r').read())
    f.close()
    return tmp_xml


# from lxml import etree
#
#
# def init_parse(file):
#     doc = etree.parse(file)
#     e = etree.XPathEvaluator(doc, namespaces={'src': 'http://www.srcML.org/srcML/src'})
#     return e
#
#
# def save_tree_to_file(doc, file):
#     with open(file, 'wb') as f:
#         f.write(etree.tostring(doc, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
#
#
# def program_transform(program_path):
#     tmp_xml = "tmp2.xml"
#     e = init_parse(program_path)
#     tree_root = e('/*')[0].getroottree()
#     save_tree_to_file(tree_root, tmp_xml)
#     open("new_tmp2.xml", 'w').write(open(program_path, 'r').read())
#     return tmp_xml