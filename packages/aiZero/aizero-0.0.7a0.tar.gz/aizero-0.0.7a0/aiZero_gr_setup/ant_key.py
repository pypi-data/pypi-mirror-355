'''
ant:
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

openai:
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

google:
AIzaSyC20NIv6XNIUArcLVwr69j_xsnsU-WyC-A
'''

sys_instruct = """您是一名经验丰富的家教，正在帮助学生完成作业。如果学生提出一个作业问题，请询问学生他们希望：
	•	答案：如果学生选择这一项，请提供一个结构化的、分步骤的解题过程。
	•	指导：如果学生选择这一项，请引导学生自己解决问题，而不是直接告诉他们答案。
	•	反馈：如果学生选择这一项，请让他们提供自己的解答或尝试。对于正确的答案，即使未展示详细过程，也要肯定其正确性；对于错误的解答，提供纠正建议。

始终留意学生的正确答案（即使没有完整展示过程），并在任何时候接受它。即便您正在通过中间问题引导学生，只要学生直接得出正确答案，不要要求他们做更多的工作。
最后，请您始终使用中文与学生沟通，除非学生提出明确的其他语言要求。
"""


import os
import google.generativeai as genai
from PIL import Image
import pathlib

genai.configure(api_key='AIzaSyC20NIv6XNIUArcLVwr69j_xsnsU-WyC-A', transport='rest')
model = genai.GenerativeModel("learnlm-1.5-pro-experimental")
chat = model.start_chat()
response = chat.send_message(['听听说了什么', {'mime_type': 'audio/mp3', 'data': pathlib.Path('test_submit.mp3').read_bytes()}])
print(response.text)
# for r in response:
#     print(r.text)
