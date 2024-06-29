from glob import glob
from lxml import etree

# 变量初始化从先定义再初始化改为定义和初始化一行解决
ns = {'src': 'http://www.srcML.org/srcML/src',
      'cpp': 'http://www.srcML.org/srcML/cpp',
      'pos': 'http://www.srcML.org/srcML/position'}
doc = None
flag = False


def init_parser(file):
    global doc
    doc = etree.parse(file)
    e = etree.XPathEvaluator(doc)
    for k, v in ns.items():
        e.register_namespace(k, v)
    return e


def get_expr(elem):
    return elem.xpath('src:expr', namespaces=ns)


def get_decl(elem):
    return elem.xpath('.//src:decl_stmt/src:decl', namespaces=ns)


def get_name(elem):
    return elem.xpath('src:name', namespaces=ns)


def save_tree_to_file(tree, file):
    with open(file, 'w') as f:
        f.write(etree.tostring(tree).decode('utf8'))


def get_funcs(e):
    return e('//src:function')


# transform variable afterwards-assignment to initialization
# int a; a = 1;
# int a = 1;
# arguments 'ignore_list' and 'instances' are pretty much legacy code and can be ignored
# argument 'e' is obtained by calling init_parser(srcML XML path)
def transform_init(e, instances=None, ignore_list=[]):
    global flag
    flag = False
    tree_root = e('/*')[0].getroottree()
    new_ignore_list = []
    separate_inits = [
        get_separate_inits(e) if instances is None else (instance[0] for instance in instances if len(instance) > 0)]
    for separate_init in separate_inits:
        for item in separate_init:
            flag = True
            decl_stmt = item[0]
            decl_elem = item[1]
            expr_stmt = item[2]
            expr_value = item[3]
            decl_stmt_prev = decl_stmt.getparent()
            decl_stmt_prev = decl_stmt_prev if decl_stmt_prev is not None else decl_stmt
            decl_stmt_prev_path = tree_root.getpath(decl_stmt_prev)
            if decl_stmt_prev_path in ignore_list: continue
            if expr_stmt.getparent() is None: continue
            # now remove the assignment statement and add initializer to the declaration
            expr_stmt.getparent().remove(expr_stmt)
            # print(''.join(decl_elem.itertext()))
            decl_name = get_name(decl_elem)[0]
            decl_name.tail = ' = ' + expr_value
    return flag, tree_root, new_ignore_list


# sanitize the assignment statements
# must be of the form 'some var = literal;'
# those passing the check will be returned in separate_inits
def judge_and_append(decl_stmt, next_stmt, decl_name, decl_elem, separate_inits):
    expr = get_expr(next_stmt)[0]
    if len(expr) != 3: return separate_inits
    tag = etree.QName(expr[2])
    if tag.localname != 'literal': return separate_inits
    if '=' not in ''.join(next_stmt.itertext()): return separate_inits
    if len(get_name(expr)) != 0:
        expr_name = get_name(expr)[0].text
        expr_value = expr[2].text
        if expr_name is None: return separate_inits
        if decl_name != expr_name: return separate_inits
        separate_inits.append((decl_stmt, decl_elem, next_stmt, expr_value))
    return separate_inits


# get all declarations with no initializer and subsequent assignment to these declared variables
def get_separate_inits(e):
    separate_inits = []
    func_elems = get_funcs(e)
    for func_elem in func_elems:
        decl_elems = get_decl(func_elem)
        for decl_elem in decl_elems:
            if '=' in ''.join(decl_elem.itertext()): continue
            decl_name = get_name(decl_elem)[0].text
            decl_stmt = decl_elem.getparent()
            next_stmt = decl_stmt.getnext()
            while next_stmt is not None:
                tag = etree.QName(next_stmt)
                if tag.localname == 'expr_stmt':
                    separate_inits = judge_and_append(decl_stmt, next_stmt, decl_name, decl_elem, separate_inits)
                next_stmt = next_stmt.getnext()
    if separate_inits == None:
        return []
    else:
        return separate_inits

def program_transform(input_xml_path,prefix):
    tmp_xml = prefix+"tmp1.xml"
    e = init_parser(input_xml_path)
    flag, transformed_tree, ignore_list = transform_init(e)
    save_tree_to_file(transformed_tree, tmp_xml)
    return tmp_xml
