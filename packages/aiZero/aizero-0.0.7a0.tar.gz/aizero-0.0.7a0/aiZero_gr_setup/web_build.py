from aiZero_gr import AIWebApp, speech_recognition, text_generation
import google.generativeai as genai
import webbrowser
import os
import json


def my_ai_function():
    text = app.input_text
    audio = app.input_audio
    if audio:
        text = speech_recognition(audio)
    response = text_generation(text, history, prompt, model="qwen-max")
    history.add_ai_content(response)
    try:
        result = json.loads(response)
        if 'code' in result:
            show_page(result['code'])
        app.send(result['text'])
    except Exception as e:
        print(str(e))
        app.send(response)


def show_page(code: str):
    """
    根据网页代码显示网页。

    :param code: 完整的网页代码字符串。
    :return: None
    """
    file_path = "generated_page.html"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)
    webbrowser.open(f"file://{os.path.abspath(file_path)}")


prompt = '''
你是一个忠实的网页设计助手，你将根据用户的需求，尽可能地生成一个能满足用户需求的网页，可能利用html+css+js的技术。
除非用户提出特殊要求，否则你设计的网页应当在满足功能要求的前提下遵循简洁、美观、现代的基本设计原则，看上去大气漂亮。
你永远仅以json数据格式返回处理结果，在"code"键中包含完整的网页代码；在"text"键中包含给予用户的任务反馈信息。
如果你无法理解用户的意图，或无法完成网页设计任务，请不要返回"code"键，而是仅包含"text"键。
最后，请注意，如果用户要求你修改代码，你必须回复完整代码而不是简略代码。
'''

app = AIWebApp(title='AI网页设计助手')
app.set_apikey('sk-5647aa1303594b73ab6cf9838bfef0d7')
history = app.create_history()
# genai.configure(api_key='AIzaSyC20NIv6XNIUArcLVwr69j_xsnsU-WyC-A', transport='rest')
# model = genai.GenerativeModel("gemini-1.5-pro", system_instruction=prompt, tools=[show_page])
# chat = model.start_chat(enable_automatic_function_calling=True)
app.add_input_text()
app.add_input_audio()
app.set_submit(my_ai_function)
app.run()
