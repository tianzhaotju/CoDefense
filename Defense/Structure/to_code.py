from pylibsrcml import srcml


def xml_to_code(xml_file,prefix):
    java_file = prefix+"file.java"
    srcml.srcml(xml_file, java_file)
    return open(java_file, 'r').read()

# import json
# import os
# import subprocess
# import time
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

# def xml_to_code(xml_file):
#     java_file = "file.java"
#     command = f'srcml "{xml_file}" -o "{java_file}" --position --src-encoding UTF-8'
#     result = cmd(command)
#
#     try:
#         if result is True:
#             with open(java_file, 'r') as file:
#                 code = file.read()
#             return code
#         else:
#             return None
#     finally:
#         if os.path.exists(java_file):
#             os.remove(java_file)
#
#         if os.path.exists(xml_file):
#             os.remove(xml_file)