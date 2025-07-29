from aiZero_gr import AIWebApp, voice_clone, speech_synthesis, text_generation
import google.generativeai as genai
from PIL import Image
import pathlib

sys_instruct = """您是一名经验丰富的家教，正在帮助学生完成作业。如果学生提出一个作业问题，请询问学生他们希望：
	•	答案：如果学生选择这一项，请提供一个结构化的、分步骤的解题过程。
	•	指导：如果学生选择这一项，请引导学生自己解决问题，而不是直接告诉他们答案。
	•	反馈：如果学生选择这一项，请让他们提供自己的解答或尝试。对于正确的答案，即使未展示详细过程，也要肯定其正确性；对于错误的解答，提供纠正建议。

始终留意学生的正确答案（即使没有完整展示过程），并在任何时候接受它。即便您正在通过中间问题引导学生，只要学生直接得出正确答案，不要要求他们做更多的工作。
最后，请您始终使用中文与学生沟通，除非学生提出明确的其他语言要求。
"""

def my_ai_function():
    text = app.input_text
    pic = app.input_pic
    audio = app.input_audio
    if pic is None and audio is None:
        response = chat.send_message(text)
        app.send(response.text)
    elif audio is None:
        response = chat.send_message([text, Image.open(pic)])
        app.send(response.text)
    elif pic is None:
        audio_type = audio.split('.')[-1]
        response = chat.send_message([text, {'mime_type': f'audio/{audio_type}',
                                             'data': pathlib.Path(audio).read_bytes()}])
        app.send(response.text)
    else:
        audio_type = audio.split('.')[-1]
        response = chat.send_message([text, Image.open(pic), {'mime_type': f'audio/{audio_type}',
                                                              'data': pathlib.Path(audio).read_bytes()}])
        app.send(response.text)


app = AIWebApp(title='AI家教——请说出关于你作业的问题')
app.set_apikey('AIzaSyC20NIv6XNIUArcLVwr69j_xsnsU-WyC-A', mode='google')
# genai.configure(api_key='AIzaSyC20NIv6XNIUArcLVwr69j_xsnsU-WyC-A', transport='rest')
model = genai.GenerativeModel("learnlm-1.5-pro-experimental", system_instruction=sys_instruct)
chat = model.start_chat()
app.add_input_text()
app.add_input_pic()
app.add_input_audio()
app.set_submit(my_ai_function)
app.run(share=True)
