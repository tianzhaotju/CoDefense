import sys
sys.path.append('./Deadcode')
from type1_if import remove_dead_code as remove_dead_code1
from type2_while import remove_dead_code as remove_dead_code2
from type3_for import remove_dead_code as remove_dead_code3
from type4_end import remove_dead_code as remove_dead_code4
from type5_block import remove_dead_code as remove_dead_code5
from type6_unused import remove_dead_code as remove_dead_code6
from type7_assert import remove_dead_code as remove_dead_code7
from type8_print import remove_dead_code as remove_dead_code8
from type9_import import remove_dead_code as remove_dead_code9

def clean_deadcode(input_code):

    output_code1 = remove_dead_code1(input_code)
    output_code2 = remove_dead_code2(output_code1)
    output_code3 = remove_dead_code3(output_code2)
    output_code4 = remove_dead_code4(output_code3)
    output_code5 = remove_dead_code5(output_code4)
    output_code6 = remove_dead_code6(output_code5)
    output_code7 = remove_dead_code7(output_code6)
    output_code8 = remove_dead_code8(output_code7)
    output_code9 = remove_dead_code9(output_code8)
    return output_code9


