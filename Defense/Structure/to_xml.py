from pylibsrcml import srcml


def code_to_xml(code, prefix):
    temp_file = prefix+"temp.java"
    open(temp_file, "w", encoding="utf-8").write(code)

    xml_file = prefix+"file.xml"
    srcml.srcml(temp_file, xml_file)
    return xml_file


# import os
# import json
# import time
# import subprocess
# from tqdm import tqdm
#
# def cmd(command):
#     try:
#         result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
#         if result.returncode != 0:
#             print("Command failed with error:", result.stderr)
#             return False
#         return True
#     except subprocess.TimeoutExpired:
#         print("Command timed out")
#         return False
#
# def code_to_xml(code):
#     temp_file = "temp.java"
#     with open(temp_file, "w", encoding="utf-8") as file:
#         file.write(code)
#
#     xml_file = "file.xml"
#
#     time0 = time.time()
#     command = f'srcml "{temp_file}" -o "{xml_file}" --position --src-encoding UTF-8'
#
#     try:
#         result = cmd(command)
#         if result is True:
#             return xml_file
#         else:
#             return None
#     finally:
#         if os.path.exists(temp_file):
#             os.remove(temp_file)
