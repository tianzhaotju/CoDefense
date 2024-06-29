from glob import glob
from lxml import etree
from lxml.etree import Element

# 多个相同变量定义从分开好几行改为一行定义完
flag = False
ns = {'src': 'http://www.srcML.org/srcML/src',
      'cpp': 'http://www.srcML.org/srcML/cpp',
      'pos': 'http://www.srcML.org/srcML/position'}

save_xml_file = './transform_xml_file/ini_var_muti'
transform_java_file = './target_author_file/transform_java/ini_var_muti'
doc = None


def init_parser(file):
    global doc
    doc = etree.parse(file)
    e = etree.XPathEvaluator(doc, namespaces=ns)
    return e


def get_b_cont(e):
    return e('//src:block_content')


def get_decl_s(elem):
    return elem.xpath('src:decl_stmt', namespaces=ns)


def get_decl_type(elem):
    return elem.xpath('src:decl/src:type/src:name', namespaces=ns)


def get_allnames(decl):
    return decl.xpath('.//src:name', namespaces=ns)


def tramsform(e, ignore_list=[], instances=None):
    global flag
    flag = False
    block_contents = [get_b_cont(e) if instances is None else (instance[0] for instance in instances)]
    tree_root = e('/*')[0].getroottree()
    new_ignore_list = []
    # Get all the block_content tags, that is, the statement block in {}
    # Traverse each {} statement block to find a separate assignment initialization statement
    for item in block_contents:
        for block_content in item:
            # Get all initialization statements under block_content
            decl_stmts = []
            vars_names = []
            # Use a list to keep only one type
            for dec_stmt in block_content:
                if dec_stmt.tag != '{http://www.srcML.org/srcML/src}decl_stmt':
                    ls = []
                    for decl_stmt in decl_stmts:
                        decl_stmt_prev = decl_stmt.getprevious()
                        decl_stmt_prev = decl_stmt_prev if decl_stmt_prev is not None else decl_stmt
                        decl_stmt_prev_path = tree_root.getpath(decl_stmt_prev)
                        if decl_stmt_prev_path in ignore_list:
                            continue
                        key = 0
                        # ------------------------------------Exclude variables used in the front when merging-----------
                        rep_var_flag = False
                        curr_names = get_allnames(decl_stmt)
                        for curr_name in curr_names:

                            if len(curr_name) == 0:
                                currname_var = ''.join(curr_name.itertext())
                                # print(currname_var)
                                if currname_var in vars_names:
                                    rep_var_flag = True

                                    break

                        for d in decl_stmt:
                            if d.tag == '{http://www.srcML.org/srcML/src}comment': continue
                            if len(d) <= 1: continue
                            if len(d[1]) == 0:
                                vars_names.append("".join(d[1].itertext()))
                            else:
                                vars_names.append("".join(d[1][0].itertext()))
                        if rep_var_flag == True: continue
                        # ----------------------------------end--------------------
                        # ---------------Handle the situation where there are multiple types of types---------
                        for decl in decl_stmt:
                            if len(decl) == 2 or len(
                                    decl) == 3:  # and decl[2][0][0].tag=='{http://www.srcML.org/srcML/src}literal'):
                                modifier_num = decl[0].xpath("src:modifier", namespaces=ns)
                                if len(modifier_num) != 0:
                                    first_mod_index = decl[0].index(modifier_num[0])
                                    modifier = Element('modifier')
                                    modifier.text = ''
                                    for modi in decl[0][first_mod_index:]:
                                        modifier.text += modi.text
                                        decl[0].remove(modi)
                                    modifier.text += ' '
                                    decl.insert(1, modifier)
                        # ----------------------------------end---------
                        if len(decl_stmt) != 0 and len(decl_stmt[0]) != 0 and len(decl_stmt[0][0]) != 0 and len(
                                decl_stmt[0][0][0]) == 0:
                            for l in ls:
                                if ''.join(decl_stmt[0][0].itertext()).replace(' ', '') == ''.join(
                                        l[0][0].itertext()).replace(' ',
                                                                    ''):  # and decl_stmt[0][0][0].text==l[0][0][0].text:
                                    flag = True

                                    decl_stmt[0].remove(decl_stmt[0][0])
                                    l.getchildren()[-1].tail = ','
                                    decl_stmt.getchildren()[0].tail = ''
                                    for children in decl_stmt.getchildren():
                                        children.tail = ''
                                        l.append(children)
                                        l.getchildren()[-1].tail = ','
                                    l.getchildren()[-1].tail = ';'
                                    key = 1
                                    break
                            if key == 0:
                                # flag is used to mark whether there is a new type to add to the list
                                ls.append(decl_stmt)
                            if flag:
                                new_ignore_list.append(decl_stmt_prev_path)
                    decl_stmts = []
                else:
                    decl_stmts.append(dec_stmt)
    return flag, tree_root, new_ignore_list


def save_file(doc, file):
    with open(file, 'w') as f:
        f.write(etree.tostring(doc).decode('utf-8'))


def program_transform(input_xml_path,prefix):
    tmp_xml = prefix+"tmp1.xml"
    e = init_parser(input_xml_path)
    flag, transformed_tree, ignore_list = tramsform(e)
    save_file(transformed_tree, tmp_xml)
    return tmp_xml
