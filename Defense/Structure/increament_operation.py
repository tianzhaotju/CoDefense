from glob import glob
from lxml import etree

# type1:i++
# type2:++i
# type3:i=i+1/i=i-1
# type4:i+=1/i-=1
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


def get_expr_stmts(e):
    return e('//src:expr_stmt')


def get_expr(elem):
    return elem.xpath('src:expr', namespaces=ns)


def get_operator(elem):
    return elem.xpath('src:operator', namespaces=ns)


def get_for_incrs(e):
    return e('//src:for/src:control/src:incr/src:expr')


def save_tree_to_file(tree, file):
    with open(file, 'w') as f:
        f.write(etree.tostring(tree).decode('utf8'))


def get_standalone_exprs(e):
    standalone_exprs = []
    # get all expression statements
    expr_stmts = get_expr_stmts(e)
    for expr_stmt in expr_stmts:
        expr = get_expr(expr_stmt)
        # there should be exactly one expression in a statement
        if len(expr) != 1: continue
        standalone_exprs.append(expr[0])
    return standalone_exprs


# type - 1: standalone statements, 2: for increments, 3: both
def get_incr_exprs(e, type):
    incr_exprs = []
    if type == 1:
        exprs = get_standalone_exprs(e)
    elif type == 2:
        exprs = get_for_incrs(e)
    elif type == 3:
        exprs = get_standalone_exprs(e) + get_for_incrs(e)
    for expr in exprs:
        opr = get_operator(expr)
        # exactly one operator, which should be ++/-- or +=/-=
        if len(opr) == 1:
            if opr[0].text == '++' or opr[0].text == '--':
                if opr[0].getparent().index(opr[0]) == 0:
                    incr_exprs.append((expr, 2))
                else:
                    incr_exprs.append((expr, 1))
            elif opr[0].text == '+=' or opr[0].text == '-=':
                token_after_opr = opr[0].getnext()
                if token_after_opr.text == '1':
                    incr_exprs.append((expr, 4))
        # two operators, e.g. i=i+1
        elif len(opr) == 2:
            if opr[0].text == '=' and (opr[1].text == '+' or opr[1].text == '-'):
                token_before_opr0 = opr[0].getprevious()
                token_after_opr0 = opr[0].getnext()
                token_after_opr1 = opr[1].getnext()
                if token_after_opr1.text == '1':
                    if ''.join(token_before_opr0.itertext()) == ''.join(token_after_opr0.itertext()):
                        incr_exprs.append((expr, 3))
    # print(incr_exprs)
    return incr_exprs


# i+=1/i-=1 to i++/i--
# type4->type1
def separate_incr_to_incr_postfix(opr):
    token_after_opr = opr[0].getnext()
    if token_after_opr is not None:
        if token_after_opr.getparent() is not None:
            if opr[0].text == '+=':
                opr[0].text = '++'
                token_after_opr.getparent().remove(token_after_opr)
            elif opr[0].text == '-=':
                opr[0].text = '--'
                token_after_opr.getparent().remove(token_after_opr)


# i+=1/i-=1 to ++i/--i
# type4->type2
def separate_incr_to_incr_prefix(opr):
    token_before_opr = opr[0].getprevious()
    token_after_opr = opr[0].getnext()
    if token_after_opr is not None:
        if opr[0].text == '+=':
            token_before_opr.text = '++' + token_before_opr.text
            token_after_opr.getparent().remove(token_after_opr)
        elif opr[0].text == '-=':
            token_before_opr.text = '--' + token_before_opr.text
            token_after_opr.getparent().remove(token_after_opr)


# i++/++i/i--/--i to i+=1/i-=1
# type1/2->type4
def incr_to_separate_incr(opr, expr):
    if opr[0].text == '++':
        opr[0].getparent().remove(opr[0])
        if expr.tail is not None:
            expr.tail = ' += 1' + expr.tail
        else:
            expr.tail = ' += 1'
    elif opr[0].text == '--':
        opr[0].getparent().remove(opr[0])
        if expr.tail is not None:
            expr.tail = ' -= 1' + expr.tail
        else:
            expr.tail = ' -= 1'


# i=i+1/i=i-1 to i+=1/i-=1
# type3->type4
def full_incr_to_separate_incr(opr, expr):
    operator = opr[1].text
    if operator == '+':
        del expr[2:4]
        opr[0].text = '+='
    elif operator == '-':
        del expr[2:4]
        opr[0].text = '-='


# the above reversed
# type4->type3
def separate_incr_to_full_incr(opr, expr):
    operator = opr[0].text
    token_before_opr = opr[0].getprevious()
    if operator == '+=':
        opr[0].text = '= ' + token_before_opr.text + ' + 1'
    elif operator == '-=':
        opr[0].text = '= ' + token_before_opr.text + ' - 1'


# i=i+1/i=i-1 to i++/++i/i--/--i
# type3->type1/2
def full_incr_to_incr(opr, expr, pre_or_post):
    operator = opr[1].text
    if expr[0].text is not None and expr[-1].text == '1':
        if operator == '+':
            del expr[1:]
            if pre_or_post == 1:
                if expr.tail is not None:
                    expr.tail = '++' + expr.tail
                else:
                    expr.tail = '++'
            else:
                expr[0].text = '++' + expr[0].text
        elif operator == '-':
            del expr[1:]
            if pre_or_post == 1:
                if expr.tail is not None:
                    expr.tail = '--' + expr.tail
                else:
                    expr.tail = '--'
            else:
                expr[0].text = '--' + expr[0].text


# type1/2->type3
def incr_to_full_incr(opr, expr, pre_or_post):
    operator = opr[0].text
    # print(pre_or_post)
    var_name = ''.join(expr[int(not pre_or_post)].itertext())
    if var_name == '++' or var_name == '--': return
    if expr[int(not pre_or_post)].text is None: return
    if operator == '++':
        del expr[pre_or_post]
        expr[0].text = var_name + ' = ' + var_name + ' + 1'
    elif operator == '--':
        del expr[pre_or_post]
        expr[0].text = var_name + ' = ' + var_name + ' - 1'


def transform(e, src_style, dst_style, ignore_list=[], instances=None):
    global flag
    flag = False
    incr_exprs = [get_standalone_exprs(e) if instances is None else (instance[0] for instance in instances)]
    tree_root = e('/*')[0].getroottree()
    new_ignore_list = []
    src_dst_tuple = (src_style, dst_style)
    for item in incr_exprs:
        for incr_expr in item:
            incr_expr_grandparent = incr_expr.getparent().getparent()
            if incr_expr_grandparent is None:
                return flag, tree_root, new_ignore_list
            incr_expr_grandparent_path = tree_root.getpath(incr_expr_grandparent)
            if incr_expr_grandparent_path in ignore_list:
                continue

            opr = get_operator(incr_expr)
            if len(opr) == 1:
                if opr[0].text == '++':
                    flag = True
                    if src_dst_tuple == ('type2', 'type1'):
                        opr[0].getparent().remove(opr[0])
                        new_opr = etree.Element('operator')
                        new_opr.text = '++'
                        incr_expr.append(new_opr)
                    elif src_dst_tuple == ('type1', 'type2'):
                        opr[0].getparent().remove(opr[0])
                        incr_expr.text = '++'
                    elif src_dst_tuple == ('type1', 'type4'):
                        incr_to_separate_incr(opr, incr_expr)
                    elif src_dst_tuple == ('type2', 'type4'):
                        incr_to_separate_incr(opr, incr_expr)
                    elif src_dst_tuple == ('type4', 'type1'):
                        separate_incr_to_incr_postfix(opr)
                    elif src_dst_tuple == ('type4', 'type2'):
                        separate_incr_to_incr_prefix(opr)
                    elif src_dst_tuple == ('type1', 'type3'):
                        incr_to_full_incr(opr, incr_expr, 1)
                    elif src_dst_tuple == ('type2', 'type3'):
                        incr_to_full_incr(opr, incr_expr, 0)
                    elif src_dst_tuple == ('type4', 'type3'):
                        separate_incr_to_full_incr(opr, incr_expr)
                elif opr[0].text == '--':
                    flag = True
                    if src_dst_tuple == ('type2', 'type1'):
                        opr[0].getparent().remove(opr[0])
                        new_opr = etree.Element('operator')
                        new_opr.text = '--'
                        incr_expr.append(new_opr)
                    elif src_dst_tuple == ('type1', 'type2'):
                        opr[0].getparent().remove(opr[0])
                        incr_expr.text = '--'
                    elif src_dst_tuple == ('type1', 'type4'):
                        incr_to_separate_incr(opr, incr_expr)
                    elif src_dst_tuple == ('type2', 'type4'):
                        incr_to_separate_incr(opr, incr_expr)
                    elif src_dst_tuple == ('type4', 'type1'):
                        separate_incr_to_incr_postfix(opr)
                    elif src_dst_tuple == ('type4', 'type2'):
                        separate_incr_to_incr_prefix(opr)
            elif len(opr) == 2:
                if src_dst_tuple == ('type3', 'type1'):
                    full_incr_to_incr(opr, incr_expr, 1)
                elif src_dst_tuple == ('type3', 'type2'):
                    full_incr_to_incr(opr, incr_expr, 0)
                elif src_dst_tuple == ('type3', 'type4'):
                    full_incr_to_separate_incr(opr, incr_expr)
            if flag:
                new_ignore_list.append(incr_expr_grandparent_path)
    return flag, tree_root, new_ignore_list


def program_transform_to1(input_xml_path,prefix):
    tmp_xml = prefix+"tmp1.xml"
    e = init_parser(input_xml_path)
    flag, transformed_tree, ignore_list = transform(e, 'type3', 'type1')
    save_tree_to_file(transformed_tree, tmp_xml)
    flag, transformed_tree, ignore_list = transform(e, 'type4', 'type1')
    save_tree_to_file(transformed_tree, tmp_xml)
    return tmp_xml


def program_transform_to2(input_xml_path,prefix):
    tmp_xml = prefix+"tmp2.xml"
    e = init_parser(input_xml_path)
    flag, transformed_tree, ignore_list = transform(e, 'type3', 'type2')
    save_tree_to_file(transformed_tree, tmp_xml)
    flag, transformed_tree, ignore_list = transform(e, 'type4', 'type2')
    save_tree_to_file(transformed_tree, tmp_xml)
    return tmp_xml


def program_transform_to3(input_xml_path,prefix):
    tmp_xml = prefix+"tmp3.xml"
    e = init_parser(input_xml_path)
    flag, transformed_tree, ignore_list = transform(e, 'type1', 'type3')
    save_tree_to_file(transformed_tree, tmp_xml)
    flag, transformed_tree, ignore_list = transform(e, 'type2', 'type3')
    save_tree_to_file(transformed_tree, tmp_xml)
    flag, transformed_tree, ignore_list = transform(e, 'type4', 'type3')
    save_tree_to_file(transformed_tree, tmp_xml)
    return tmp_xml


def program_transform_to4(input_xml_path,prefix):
    tmp_xml = prefix+"tmp4.xml"
    e = init_parser(input_xml_path)
    flag, transformed_tree, ignore_list = transform(e, 'type1', 'type4')
    save_tree_to_file(transformed_tree, tmp_xml)
    flag, transformed_tree, ignore_list = transform(e, 'type2', 'type4')
    save_tree_to_file(transformed_tree, tmp_xml)
    flag, transformed_tree, ignore_list = transform(e, 'type3', 'type4')
    save_tree_to_file(transformed_tree, tmp_xml)
    return tmp_xml
