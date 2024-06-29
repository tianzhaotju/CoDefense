import os
import sys
import time

sys.path.append('./python_parser/')
from run_parser import is_valid_variable_name, extract_dataflow, unique
import numpy as np
from to_code import xml_to_code
from to_xml import code_to_xml


def get_double_code_quality(xml1, xml2, code_quality_history, prefix, language='java'):
    # 如果返回值 score>0 则选择code2，否则保持code1不变
    code1 = xml_to_code(xml1, prefix)
    code2 = xml_to_code(xml2, prefix)

    k1 = code1.strip()
    if k1 in code_quality_history:
        score1_list = code_quality_history[k1]
    else:
        score1_list = get_code_quality(code1)
        code_quality_history[k1] = score1_list

    k2 = code2.strip()
    if k2 in code_quality_history:
        score2_list = code_quality_history[k2]
    else:
        score2_list = get_code_quality(code2)
        code_quality_history[k2] = score2_list

    score_list = []
    for i in range(9):
        v1, v2 = score1_list[i], score2_list[i]
        if v1 == -1 or v2 == -1:
            score_list.append(0)
            continue
        elif i < 6:
            if v1 == 0 and v2 ==0:
                score_list.append(0)
                continue
            elif v1 == 0 and v2 != 0:
                v1, v2 = v1+1, v2+1
            score_list.append((v1-v2)/v1)
        elif i < 9:
            if v1 == 0 and v2 ==0:
                score_list.append(0)
                continue
            elif v1 == 0 and v2 != 0:
                v1, v2 = v1+1, v2+1
            score_list.append((v2-v1)/v1)
    score_list = np.array(score_list)
    score = np.average([score_list[0], np.average(score_list[1:6]), np.average(score_list[6:])])

    if score > 0:
        return xml2, code_quality_history
    else:
        return xml1, code_quality_history


def get_code_quality(code1, language='java'):
    score_list = []
    ###############################
    # Code Complexity
    ###############################
    dfg1, index_table1, code_tokens1 = extract_dataflow(code1, language)
    identifiers1 = set()
    E1 = len(dfg1)
    N1_set = set()
    for d in dfg1:
        if is_valid_variable_name(d[0], language):
            identifiers1.add(d[0])
        try:
            N1_set.add(d[0])
        except:
            pass
        try:
            for i in d[3]:
                N1_set.add(i)
        except:
            pass
    identifiers1 = list(identifiers1)
    N1 = len(N1_set)
    VG1 = E1 - N1 + 2
    score_list.append(VG1)

    ###############################
    # Code Readability B&W
    ###############################
    BW = 0
    score_list.append(len(identifiers1))

    try:
        score_list.append(len(code_tokens1) / (len(code1.split(';')) + 2))
    except:
        score_list.append(-1)

    try:
        score_list.append((code_tokens1.count('(') + code_tokens1.count('{')) / (len(code1.split(';')) + 2))
    except:
        score_list.append(-1)

    try:
        len1 = 1
        start = 0
        for i in range(len(code_tokens1)):
            if code_tokens1[i] == ';':
                len1 = max(len1, i - start + 1)
                start = i + 1
            if i == len(code_tokens1) - 1:
                len1 = max(len1, i - start + 1)
        score_list.append(len1)
    except:
        score_list.append(-1)

    try:
        score_list.append(code_tokens1.count('.') / (len(code1.split(';')) + 2))
    except:
        score_list.append(-1)

    ###############################
    # Code Readability TC
    ###############################
    try:
        stack = []
        blocks1 = []
        for i, char in enumerate(code_tokens1):
            if char == '{':
                stack.append(i)
            elif char == '}':
                if stack:
                    block_start = stack.pop()
                    blocks1.append(code_tokens1[block_start:i + 1])
        if len(blocks1) > 1:
            tc_list1 = []
            for i in range(len(blocks1) - 1):
                for j in range(i + 1, len(blocks1)):
                    intersection = set(blocks1[i]).intersection(set(blocks1[j]))
                    union = set(blocks1[i]).union(set(blocks1[j]))
                    tc_list1.append((len(intersection) + 1) / (len(union) + 1))
            score_list.append(np.max(tc_list1))
            score_list.append(np.mean(tc_list1))
            score_list.append(np.min(tc_list1))
        else:
            while len(score_list) < 9:
                score_list.append(-1)
    except:
        while len(score_list) < 9:
            score_list.append(-1)

    return score_list


# def get_code_quality(xml1, xml2, language='java'):
#     # 如果返回值 score>0 则选择code2，否则保持code1不变
#     time0 = time.time()
#     code1 = xml_to_code(xml1)
#     code2 = xml_to_code(xml2)
#     print('################ 000000', time.time()-time0)
#     time0 = time.time()
#     ###############################
#     # Code Complexity
#     ###############################
#     dfg1, index_table1, code_tokens1 = extract_dataflow(code1, language)
#     print('################ aaaaaaaaaa', time.time() - time0)
#     time0 = time.time()
#     identifiers1 = []
#     for d in dfg1:
#         if is_valid_variable_name(d[0], language):
#             identifiers1.append(d[0])
#     identifiers1 = unique(identifiers1)
#
#     E1 = len(dfg1)
#     N1_set = set()
#     for d in dfg1:
#         for i in range(len(d)):
#             if i == 0:
#                 if is_valid_variable_name(d[i], language):
#                     N1_set.add(d[i])
#             elif i == 1 or i == 2:
#                 continue
#             elif i > 2:
#                 try:
#                     if is_valid_variable_name(d[i][0], language):
#                         N1_set.add(d[i][0])
#                 except:
#                     pass
#     N1 = len(N1_set)
#
#     dfg2, index_table2, code_tokens2 = extract_dataflow(code2, language)
#     identifiers2 = []
#     for d in dfg2:
#         if is_valid_variable_name(d[0], language):
#             identifiers2.append(d[0])
#     identifiers2 = unique(identifiers2)
#
#     E2 = len(dfg2)
#     N2_set = set()
#     for d in dfg2:
#         for i in range(len(d)):
#             if i == 0:
#                 if is_valid_variable_name(d[i], language):
#                     N2_set.add(d[i])
#             elif i == 1 or i == 2:
#                 continue
#             elif i > 2:
#                 try:
#                     if is_valid_variable_name(d[i][0], language):
#                         N2_set.add(d[i][0])
#                 except:
#                     pass
#     N2 = len(N2_set)
#
#     VG1 = E1 - N1 + 2
#     VG2 = E2 - N2 + 2
#
#     if VG1 == 0:
#         VG1 = 1
#         if VG2 == 0:
#             VG2 = 1
#     VG = (VG1 - VG2) / VG1
#
#     ###############################
#     # Code Readability B&W
#     ###############################
#     BW = 0
#     try:
#         len1 = len(identifiers1)
#         len2 = len(identifiers2)
#         if len1 == 0:
#             len1 = 1
#             if len2 == 0:
#                 len2 = 1
#         BW += (len1 - len2) / len1
#     except:
#         pass
#
#     try:
#         len1 = len(code_tokens1) / (len(code1.split(';')) + 2)
#         len2 = len(code_tokens2) / (len(code2.split(';')) + 2)
#         BW += (len1 - len2) / len1
#     except:
#         pass
#
#     try:
#         len1 = (code_tokens1.count('(') + code_tokens1.count('{')) / (len(code1.split(';')) + 2)
#         len2 = (code_tokens2.count('(') + code_tokens2.count('{')) / (len(code2.split(';')) + 2)
#         if len1 == 0:
#             len1 = 1
#             if len2 == 0:
#                 len2 = 1
#         BW += (len1 - len2) / len1
#     except:
#         pass
#
#     try:
#         len1 = 1
#         start = 0
#         for i in range(len(code_tokens1)):
#             if code_tokens1[i] == ';':
#                 len1 = max(len1, i - start + 1)
#                 start = i + 1
#             if i == len(code_tokens1) - 1:
#                 len1 = max(len1, i - start + 1)
#         len2 = 1
#         start = 0
#         for i in range(len(code_tokens2)):
#             if code_tokens2[i] == ';':
#                 len2 = max(len2, i - start + 1)
#                 start = i + 1
#             if i == len(code_tokens2) - 1:
#                 len2 = max(len2, i - start + 1)
#         if len1 == 0:
#             len1 = 1
#             if len2 == 0:
#                 len2 = 1
#         BW += (len1 - len2) / len1
#     except:
#         pass
#
#     try:
#         len1 = code_tokens1.count('.') / (len(code1.split(';')) + 2)
#         len2 = code_tokens2.count('.') / (len(code2.split(';')) + 2)
#         if len1 == 0:
#             len1 = 1
#             if len2 == 0:
#                 len2 = 1
#         BW += (len1 - len2) / len1
#     except:
#         pass
#
#     ###############################
#     # Code Readability TC
#     ###############################
#     TC = 0
#     try:
#         stack = []
#         blocks1 = []
#         for i, char in enumerate(code_tokens1):
#             if char == '{':
#                 stack.append(i)
#             elif char == '}':
#                 if stack:
#                     block_start = stack.pop()
#                     blocks1.append(code_tokens1[block_start:i + 1])
#
#         stack = []
#         blocks2 = []
#         for i, char in enumerate(code_tokens2):
#             if char == '{':
#                 stack.append(i)
#             elif char == '}':
#                 if stack:
#                     block_start = stack.pop()
#                     blocks2.append(code_tokens2[block_start:i + 1])
#
#         if len(blocks1) > 1 and len(blocks2) > 1:
#             tc_list1 = []
#             for i in range(len(blocks1) - 1):
#                 for j in range(i + 1, len(blocks1)):
#                     intersection = set(blocks1[i]).intersection(set(blocks1[j]))
#                     union = set(blocks1[i]).union(set(blocks1[j]))
#                     tc_list1.append((len(intersection) + 1) / (len(union) + 1))
#
#             tc_list2 = []
#             for i in range(len(blocks2) - 1):
#                 for j in range(i + 1, len(blocks2)):
#                     intersection = set(blocks2[i]).intersection(set(blocks2[j]))
#                     union = set(blocks2[i]).union(set(blocks2[j]))
#                     tc_list2.append((len(intersection) + 1) / (len(union) + 1))
#
#             max_tc1 = np.max(tc_list1)
#             max_tc2 = np.max(tc_list2)
#             avg_tc1 = np.mean(tc_list1)
#             avg_tc2 = np.mean(tc_list2)
#             min_tc1 = np.min(tc_list1)
#             min_tc2 = np.min(tc_list2)
#
#             if max_tc1 == 0:
#                 max_tc1 = 1
#                 if max_tc2 == 0:
#                     max_tc2 = 1
#             TC += (max_tc2 - max_tc1) / max_tc1
#
#             if avg_tc1 == 0:
#                 avg_tc1 = 1
#                 if avg_tc2 == 0:
#                     avg_tc2 = 1
#             TC += (avg_tc2 - avg_tc1) / avg_tc1
#
#             if min_tc1 == 0:
#                 min_tc1 = 1
#                 if min_tc2 == 0:
#                     min_tc2 = 1
#             TC += (min_tc2 - min_tc1) / min_tc1
#     except:
#         pass
#
#     score = (VG + (BW / 5.) + (TC / 3.)) / 3.
#
#     print('################ 1111111', time.time() - time0)
#
#     if score > 0.:
#         return code_to_xml(code2)
#     else:
#         return code_to_xml(code1)
