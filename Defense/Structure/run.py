import sys
import time

sys.path.append('./Structure')
from to_xml import code_to_xml
from to_code import xml_to_code
from code_quality import get_double_code_quality
from copy_file import program_transform as copy_file

from assigncombine_to_assignspilt import program_transform as assigncombine_to_assignspilt
from assignspilt_to_assigncombine import program_transform as assignspilt_to_assigncombine

from for_to_while import program_transform as for_to_while
from while_to_for import program_transform as while_to_for

from ifcombine_to_ifspilt import program_transform as ifcombine_to_ifspilt
from ifspilt_to_ifcombine import program_transform as ifspilt_to_ifcombine

from varinitahead_to_varinituse import program_transform as varinitahead_to_varinituse
from varinituse_to_varinitahead import program_transform as varinituse_to_varinitahead

from varinitmerge_to_varinitpos import program_transform as varinitmerge_to_varinitpos
from varinitpos_to_varinitmerge import program_transform as varinitpos_to_varinitmerge

from varinitmultiple_to_varinitsame import program_transform as varinitmultiple_to_varinitsame
from varinitsame_to_varinitmultiple import program_transform as varinitsame_to_varinitmultiple

from upper_data import program_transform as upper_data

from converse_negative import program_transform as converse_negative

from omitted_curlybraces import program_transform as omitted_curlybraces

from operator_swap import program_transform as operator_swap

from assign_constant import program_transform as assign_constant

from increament_operation import program_transform_to1,program_transform_to2,program_transform_to3,program_transform_to4


def structure(input_code, prefix=''):
    code_quality_history = {}
    xml_list = []
    try:
        xml_file = code_to_xml(input_code, prefix)
        xml_list.append(xml_file)
    except:
        print(0)
        return input_code

    try:
        xml_file, code_quality_history = get_double_code_quality(assigncombine_to_assignspilt(xml_file, prefix),assignspilt_to_assigncombine(xml_file,prefix), code_quality_history, prefix)
        xml_list.append(xml_file)
    except:
        print(1)
        pass

    try:
        xml_file, code_quality_history = get_double_code_quality(while_to_for(xml_file, prefix),for_to_while(xml_file, prefix), code_quality_history, prefix)
        xml_list.append(xml_file)
    except:
        print(2)
        pass

    try:
        xml_file, code_quality_history = get_double_code_quality(ifcombine_to_ifspilt(xml_file,prefix), ifspilt_to_ifcombine(xml_file,prefix), code_quality_history, prefix)
        xml_list.append(xml_file)
    except:
        print(3)
        pass

    try:
        xml_file, code_quality_history = get_double_code_quality(varinitahead_to_varinituse(xml_file,prefix), varinituse_to_varinitahead(xml_file,prefix), code_quality_history, prefix)
        xml_list.append(xml_file)
    except:
        print(4)
        pass

    try:
        xml_file, code_quality_history = get_double_code_quality(varinitmerge_to_varinitpos(xml_file,prefix), varinitpos_to_varinitmerge(xml_file,prefix), code_quality_history, prefix)
        xml_list.append(xml_file)
    except:
        print(5)
        pass

    try:
        xml_file, code_quality_history = get_double_code_quality(varinitmultiple_to_varinitsame(xml_file,prefix), varinitsame_to_varinitmultiple(xml_file,prefix), code_quality_history, prefix)
        xml_list.append(xml_file)
    except:
        print(6)
        pass

    try:
        xml_file, code_quality_history = get_double_code_quality(upper_data(xml_file,prefix), copy_file(xml_file,prefix), code_quality_history, prefix) # copy函数用于创造一个临时的xml文件，避免不操作的时候直接删除掉file.xml文件
        xml_list.append(xml_file)
    except:
        print(7)
        pass

    try:
        xml_file, code_quality_history = get_double_code_quality(converse_negative(xml_file,prefix), copy_file(xml_file,prefix), code_quality_history, prefix)
        xml_list.append(xml_file)
    except:
        print(8)
        pass

    try:
        xml_file, code_quality_history = get_double_code_quality(omitted_curlybraces(xml_file,prefix), copy_file(xml_file,prefix), code_quality_history, prefix)
        xml_list.append(xml_file)
    except:
        print(9)
        pass

    try:
        xml_file, code_quality_history = get_double_code_quality(operator_swap(xml_file,prefix), copy_file(xml_file,prefix), code_quality_history, prefix)
        xml_list.append(xml_file)
    except:
        print(10)
        pass

    try:
        xml_file, code_quality_history = get_double_code_quality(assign_constant(xml_file,prefix), copy_file(xml_file,prefix), code_quality_history, prefix)
        xml_list.append(xml_file)
    except:
        print(11)
        pass

    try:
        xml_file, code_quality_history = get_double_code_quality(program_transform_to1(xml_file,prefix), program_transform_to2(xml_file,prefix), code_quality_history, prefix)
        xml_list.append(xml_file)
    except:
        print(12)
        pass

    try:
        tmp = copy_file(xml_file,prefix)# 保留一下文件12以便后续比较
        xml_list.append(tmp)
    except:
        print(13)
        pass

    try:
        xml_file, code_quality_history = get_double_code_quality(program_transform_to3(xml_file,prefix), program_transform_to4(xml_file,prefix), code_quality_history, prefix)
        xml_list.append(xml_file)
    except:
        print(14)
        pass

    try:
        xml_file, code_quality_history = get_double_code_quality(tmp, xml_file, code_quality_history, prefix)
        xml_list.append(xml_file)
    except:
        print(15)
        pass

    try:
        output_code = xml_to_code(xml_file, prefix)
        return output_code
    except:
        return input_code