import gradio as gr
import dashscope
from http import HTTPStatus
import base64
import requests
import time
from pathlib import Path
import os
from dashscope.audio.tts_v2 import *
import threading
import queue


RESOURCE_PATH = Path(__file__).parent.resolve()


def resolve_resource_path(path):
    """
    解析资源路径：将相对路径与应用的资源路径结合，返回绝对路径。

    参数:
    path (str): 相对资源路径。

    返回:
    Path: 绝对资源路径。
    """
    return Path(RESOURCE_PATH / path).resolve()


def file_to_base64(path):
    with open(path, 'rb') as file:
        encoded_string = base64.b64encode(file.read())
    return encoded_string.decode('utf-8')


def upload_file(file_path):
    """
    上传文件到服务器。

    参数:
    file_path: 文件路径，本地路径或网络URL。

    返回值:
    上传后的文件URL或错误信息。
    """
    file_path = str(resolve_resource_path(file_path))
    if not os.path.exists(file_path):
        return file_path
    upload_url = 'http://47.99.81.126:6500/upload'
    with open(file_path, 'rb') as file:
        files = {'file': file}
        try:
            response = requests.post(upload_url, files=files)
            # 检查请求是否成功
            if response.status_code == 200:
                data = response.json()
                return data['url']
            else:
                raise Exception(
                    'Error Message: {}, Status Code: {}, Response: {}'.format('文件上传失败', response.status_code,
                                                                              response.text))
        except Exception as e:
            raise Exception(f"An error occurred: {e}")


# 大模型文字交互
def text_generation(text, chat_history=[], prompt='你是一个人工智能助手，你的名字叫小H', stream=False, model='qwen-plus'):
    """
    与大模型进行文字交互，基于给定的对话历史和提示进行响应生成。

    参数:
    text (str): 本次提交的用户对话内容。
    chat_history (list): 对话历史，每个元素为用户或助手的一条消息。
    prompt (str): 提示文本，用于引导模型的响应，默认为"你是一个人工智能助手，你的名字叫小H"。
    stream (bool): 是否以流式方式获取生成结果，默认为False。
    model (str): 模型名，默认为"qwen-plus"。

    返回:
    str: 模型生成的响应文本，或错误信息。
    """

    def generator():
        for r in response:
            if r.status_code == HTTPStatus.OK:
                yield r.output.choices[0]['message']['content']
            else:
                return "错误: " + r.message

    try:
        messages = [{'role': 'system', 'content': prompt}]
        for message in chat_history:
            if isinstance(message['content'], str):
                if '[AI图像]' not in message['content'] and '<audio controls autoplay>' not in message['content']:
                    messages.append({'role': message['role'], 'content': message['content']})
        messages.append({'role': 'user', 'content': text})
        if stream:
            response = dashscope.Generation.call(model=model,
                                                 messages=messages,
                                                 result_format='message',
                                                 stream=stream,
                                                 incremental_output=True)
            return generator()
        else:
            response = dashscope.Generation.call(model=model,
                                                 messages=messages,
                                                 result_format='message',
                                                 stream=stream)
            if response.status_code == HTTPStatus.OK:
                return response.output.choices[0]['message']['content']
            else:
                return "错误: " + response.message
    except Exception as e:
        return "错误: " + str(e)


# 大模型图像理解
def image_understanding(img, text="", chat_history=[], prompt='你是一名人工智能助手', stream=False, model='qwen-vl-plus'):
    """
    大模型对图像进行理解，基于对话历史和图像进行响应生成。

    参数:
    img (str): 图像的本地路径或URL。
    text (str): 与图像同时提交的文本内容。
    chat_history (list): 对话历史，每个元素为用户或助手的一条消息。
    prompt (str): 提示文本，用于引导模型的响应，默认为"你是一名人工智能助手"。
    stream (bool): 是否以流式方式获取生成结果，默认为False。
    model (str): 模型名，默认为"qwen-vl-plus"。

    返回:
    str: 模型生成的响应文本，或错误信息。
    """
    def generator():
        # 生成器，用于流式返回响应
        for r in response:
            if r.status_code == HTTPStatus.OK:
                yield r.output.choices[0].message.content[0]['text']
            else:
                return "错误: " + r.message
    try:
        messages = [{'role': 'system', 'content': [{'text': prompt}]}]
        for message in chat_history:
            if isinstance(message['content'], dict):
                messages.append({'role': message['role'], 'content': [{'image': f"file://{message['content']['path']}"}]})
            elif not isinstance(message['content'], str):
                url = f"file://{message['content'].file.path}"
                messages.append({'role': message['role'], 'content': [{'image': url}]})
            else:
                messages.append({'role': message['role'], 'content': [{'text': message['content']}]})
        if img:
            messages.append({'role': 'user', 'content': [{'image': f"file://{img}"}, {'text': text}]})
        if stream:
            response = dashscope.MultiModalConversation.call(model=model,
                                                             messages=messages,
                                                             stream=stream, incremental_output=True)
            return generator()
        else:
            response = dashscope.MultiModalConversation.call(model=model,
                                                             messages=messages)
            if response.status_code == HTTPStatus.OK:
                return response.output.choices[0].message.content[0]['text']
            else:
                return "错误: " + response.message
    except Exception as e:
        return "错误: " + str(e)


# 大模型声音理解
def audio_understanding(audio, text="", chat_history=[], prompt='你是一名人工智能助手', stream=False, model='qwen-audio-turbo'):
    """
    大模型对声音进行理解，基于对话历史和音频进行响应生成。

    参数:
    audio (str): 音频的本地路径或URL。
    text (str): 与音频同时提交的文本内容。
    chat_history (list): 对话历史，每个元素为用户或助手的一条消息。
    prompt (str): 提示文本，用于引导模型的响应，默认为"你是一名人工智能助手"。
    stream (bool): 是否以流式方式获取生成结果，默认为False。
    model (str): 模型名，默认为"qwen-audio-turbo"。

    返回:
    str: 模型生成的响应文本，或错误信息。
    """
    def generator():
        # 生成器，用于流式返回响应
        for r in response:
            if r.status_code == HTTPStatus.OK:
                yield r.output.choices[0].message.content[0]['text']
            else:
                return "错误: " + r.message
    try:
        messages = [{'role': 'system', 'content': [{'text': prompt}]}]
        for message in chat_history:
            if isinstance(message['content'], dict):
                messages.append({'role': message['role'], 'content': [{'audio': f"file://{message['content']['path']}"}]})
            elif not isinstance(message['content'], str):
                url = f"file://{message['content'].file.path}"
                messages.append({'role': message['role'], 'content': [{'audio': url}]})
            else:
                if len(messages[-1]['content']) == 1 and 'audio' in messages[-1]['content'][0]:
                    messages[-1]['content'].append({'text': message['content']})
                else:
                    messages.append({'role': message['role'], 'content': [{'text': message['content']}]})
        if audio:
            messages.append({'role': 'user', 'content': [{'audio': f'file://{audio}'}, {'text': text}]})
        if stream:
            response = dashscope.MultiModalConversation.call(model=model,
                                                             messages=messages,
                                                             stream=stream, incremental_output=True)
            return generator()
        else:
            response = dashscope.MultiModalConversation.call(model=model,
                                                             messages=messages)
            if response.status_code == HTTPStatus.OK:
                return response.output.choices[0].message.content[0]['text']
            else:
                return "错误: " + response.message
    except Exception as e:
        return "错误: " + str(e)


# 大模型图像生成
def image_generation(prompt, model='wanx-v1', size='1024*1024'):
    """
    根据提示文本生成图像。

    参数:
    prompt (str): 提示文本，用于指导图像生成。
    model (str): 模型名，默认为"wanx-v1"。
    size (str): 生成的图像尺寸，默认为"1024*1024"，参数值必须满足模型可输出的尺寸要求。

    返回:
    str: 生成的图像URL，或错误信息。
    """
    try:
        response = dashscope.ImageSynthesis.async_call(model=model,
                                                       prompt=prompt,
                                                       n=1,
                                                       size=size)
        if response.status_code == HTTPStatus.OK:
            rsp = dashscope.ImageSynthesis.wait(response)
            if rsp.status_code == HTTPStatus.OK:
                return rsp.output.results[0].url
            else:
                return "错误: " + response.message
        else:
            return "错误: " + response.message
    except Exception as e:
        return "错误: " + str(e)


# 大模型人像风格重绘
def human_repaint(img, style=7, model='wanx-style-repaint-v1'):
    """
    使用大模型对人像图片进行风格重绘。

    参数:
    img (str): 图像文件，本地路径或网络URL。
    style (int): 风格指数，默认为7。
    model (str): 模型名，默认为"wanx-style-repaint-v1"。

    返回值:
    重绘后的图像URL或错误信息。
    """
    try:
        img_url = upload_file(img)
        url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': dashscope.api_key,
            'X-DashScope-Async': 'enable',
            'X-DashScope-OssResourceResolve': 'enable'
        }

        params = {
            'model': model,
            'input': {
                'image_url': img_url,
                'style_index': style
            }
        }

        response = requests.post(url, headers=headers, json=params)
        if response.status_code == 200:
            task_id = response.json()['output']['task_id']
            # 异步任务，轮询任务状态直到完成或失败
            while True:
                time.sleep(3)
                response = requests.get('https://dashscope.aliyuncs.com/api/v1/tasks/{}'.format(task_id),
                                        headers={'Authorization': dashscope.api_key})
                if response.status_code == 200:
                    if response.json()['output']['task_status'] == 'SUCCEEDED':
                        return response.json()['output']['results'][0]['url']
                    elif response.json()['output']['task_status'] == 'FAILED':
                        return "错误: " + response.json()['output']['message']
                else:
                    return "错误: " + response.json()['message']
        else:
            return "错误: " + response.json()['message']
    except Exception as e:
        return "错误: " + str(e)


# 涂鸦作画
def sketch_to_image(img, prompt, style='<anime>', model='wanx-sketch-to-image-lite'):
    """
    将涂鸦图像转换为现实图像。

    参数:
    img (str): 涂鸦图像文件，本地路径或网络URL。
    prompt (str): 描述期望图像的文字提示。
    style (str): 风格标签，默认为'<anime>'。
    model (str): 模型名，默认为"wanx-sketch-to-image-lite"。

    返回值:
    生成的图像URL或错误信息。
    """
    try:
        img_url = upload_file(img)  # 上传图像文件
        url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-synthesis/'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': dashscope.api_key,
            'X-DashScope-Async': 'enable',
            'X-DashScope-OssResourceResolve': 'enable'
        }

        params = {
            'model': model,
            'input': {
                'sketch_image_url': img_url,
                'prompt': prompt
            },
            'parameters': {
                'size': '768*768',
                'n': 1,
                'style': style
            }
        }

        response = requests.post(url, headers=headers, json=params)
        if response.status_code == 200:
            task_id = response.json()['output']['task_id']
            # 异步任务，轮询任务状态直到完成或失败
            while True:
                time.sleep(3)
                response = requests.get('https://dashscope.aliyuncs.com/api/v1/tasks/{}'.format(task_id),
                                        headers={'Authorization': dashscope.api_key})
                if response.status_code == 200:
                    if response.json()['output']['task_status'] == 'SUCCEEDED':
                        return response.json()['output']['results'][0]['url']
                    elif response.json()['output']['task_status'] == 'FAILED':
                        return "错误: " + response.json()['output']['message']
                else:
                    return "错误: " + response.json()['message']
        else:
            return "错误: " + response.json()['message']
    except Exception as e:
        return "错误: " + str(e)


# 语音识别
def speech_recognition(audio, model='paraformer-v2'):
    """
    将语音转换为文字。

    参数:
    audio (str): 语音文件，本地路径或网络URL。
    model (str): 模型名，默认为"paraformer-v2"。

    返回值:
    识别出的文字或错误信息。
    """
    try:
        audio_url = upload_file(audio)  # 上传语音文件
        task_response = dashscope.audio.asr.Transcription.async_call(
            model=model,
            file_urls=[audio_url]
        )
        transcribe_response = dashscope.audio.asr.Transcription.wait(task=task_response.output.task_id)
        if transcribe_response.status_code == HTTPStatus.OK:
            result = transcribe_response.output
            if result['task_status'] == 'SUCCEEDED':
                json_url = result['results'][0]['transcription_url']
                response = requests.get(json_url)
                if response.status_code == 200:
                    data = response.json()
                    return data['transcripts'][0]['text']
                else:
                    return '错误: 结果获取出错'
            else:
                return '错误: 解码错误'
        else:
            return '错误: 解析错误'
    except Exception as e:
        return "错误: " + str(e)


# 语音合成
def speech_synthesis(text, rate=1.0, pitch=1.0, voice='longxiaochun', model='cosyvoice-v1'):
    """
    将文字转换为语音。

    参数:
    text (str): 要合成的文字。
    rate (float): 语速调整，默认为1，范围0.5-2。
    pitch (float): 语调调整，默认为1，范围0.5-2。
    voice (str): 语音音色名，默认为'longxiaochun'。
    model (str): 模型名，默认为'cosyvoice-v1'。

    返回值:
    合成的语音二进制数据经base64编码后的结果或错误信息。
    """
    try:
        synthesizer = SpeechSynthesizer(model=model, voice=voice, pitch_rate=pitch, speech_rate=rate)
        result = synthesizer.call(text)
        return base64.b64encode(result).decode('utf-8')
    except Exception as e:
        return "错误: " + str(e)


# 声音克隆
def voice_clone(audio, prefix='prefix', model='cosyvoice-clone-v1'):
    """
    克隆音频中的语音音色。

    参数:
    audio (str): 被克隆的语音音频文件路径或url。
    prefix (str): 自定义音色前缀，仅允许数字和小写字母，小于十个字符。默认为'prefix'。
    model (str): 模型名，默认为'cosyvoice-clone-v1'。

    返回值:
    获取的音色名，可进一步用于speech_synthesis函数。
    """
    try:
        audio_url = upload_file(audio)  # 上传语音文件
        service = VoiceEnrollmentService()
        voice_id = service.create_voice(target_model=model, prefix=prefix, url=audio_url)
        return voice_id
    except Exception as e:
        return "错误: " + str(e)


class ChatHistory(list):
    def __init__(self):
        super().__init__()

    def add_content(self, role, content, type='text'):
        if type == 'text':
            self.append({'role': role, 'content': content})
        else:
            self.append({'role': role, 'content': {type: content}})

    def add_user_content(self, content, type='text'):
        """
        添加用户发起的对话历史内容。

        参数:
        content (str): 匹配类型的对话内容。
        type (str): 类型，默认为'text'。
        """
        self.add_content('user', content, type)

    def add_ai_content(self, content, type='text'):
        """
        添加AI发起的对话历史内容。

        参数:
        content (str): 匹配类型的对话内容。
        type (str): 类型，默认为'text'。
        """
        self.add_content('assistant', content, type)


class AIWebApp:
    def __init__(self, title='My AI Web App'):
        self.title = title
        self.components = []
        self.core_logic = None
        self.api_key = None
        self.mode = None
        self.client = None

        # 用于存储输入数据的属性
        self.input_text = ''
        self.input_pic = None
        self.input_audio = None
        self.chat_history = []

        # 用于存储处理结果的字典
        self.results = {}

        # 用于流式输出的队列
        self.output_queue = queue.Queue()

    def create_history(self):
        """
        创建空的自定义对话历史记录对象。
        """
        return ChatHistory()

    @classmethod
    def set_apikey(cls, key):
        """
        设置API KEY。

        参数:
        key (str): dashscope的API KEY。
        """
        cls.api_key = key
        dashscope.api_key = key
        cls.mode = 'dashscope'

    def add_input_text(self):
        """
        添加文字输入框组件。
        """
        self.components.append({
            'component': gr.Textbox,
            'kwargs': {'label': '文字输入'}
        })

    def add_input_pic(self):
        """
        添加图像输入框组件。
        """
        self.components.append({
            'component': gr.Image,
            'kwargs': {'label': '图像输入', 'type': 'filepath', 'height': 280, 'sources': ['webcam', 'upload']}
        })

    def add_input_audio(self):
        """
        添加音频输入框组件。
        """
        self.components.append({
            'component': gr.Audio,
            'kwargs': {'label': '音频输入', 'type': 'filepath', 'sources': ['microphone', 'upload']}
        })

    def set_submit(self, callback=None):
        """
        设置提交按钮的功能函数。

        参数:
        callback: 功能函数的名称，默认为None。
        """
        self.core_logic = callback

    def send(self, content, type='text'):
        """
        将AI返回结果推送到聊天框。

        参数:
        content (str): 匹配类型的对话内容。
        type (str): 类型，默认为'text'。
        """
        self.output_queue.put({type: content})

    def run(self, **kwargs):
        """
        启动AI Web应用。
        可设置参数与gr.Blocks().launch()方法相同。
        """
        with gr.Blocks(title=self.title) as demo:
            gr.Markdown(f"# {self.title}")
            state = gr.State([])  # 用于存储多轮对话的状态

            with gr.Row():
                with gr.Column(scale=2):
                    inputs = []
                    with gr.Row():
                        clear_button = gr.ClearButton(value='清除输入')
                        submit_button = gr.Button('提交', variant='primary')
                    for comp_def in self.components:
                        component_class = comp_def['component']
                        component_kwargs = comp_def.get('kwargs', {})
                        component_instance = component_class(**component_kwargs)
                        inputs.append(component_instance)
                        clear_button.add(component_instance)

                # 显示对话历史的组件
                chat_history = gr.Chatbot(type='messages', label='对话记录', show_copy_button=True,
                                          height='85vh', scale=3,
                                          latex_delimiters=[{"left": '\\[', "right": '\\]', "display": True},
                                                            {"left": '\\(', "right": '\\)', "display": False},
                                                            {"left": '$$', "right": '$$', "display": True}])

            def gradio_callback(*args):
                # 提取输入参数和状态
                *user_inputs, chat_history_state = args

                self.chat_history = chat_history_state
                # 重置输入属性
                self.input_text = ''
                self.input_pic = None
                self.input_audio = None

                # 根据添加的组件，按顺序获取输入数据并存储到属性中
                idx = 0
                for comp_def in self.components:
                    component_class = comp_def['component']
                    comp_name = component_class.__name__
                    if comp_name == 'Textbox':
                        self.input_text = user_inputs[idx]
                        idx += 1
                    elif comp_name == 'Image':
                        self.input_pic = user_inputs[idx]
                        idx += 1
                    elif comp_name == 'Audio':
                        self.input_audio = user_inputs[idx]
                        idx += 1

                # 初始化对话历史
                if not chat_history_state:
                    chat_history_state = []

                # 构建用户的多模态输入消息
                if self.input_pic:
                    chat_history_state.append({"role": "user", "content": {"path": self.input_pic, "alt_text": "用户输入图像"}})
                if self.input_audio:
                    chat_history_state.append({"role": "user", "content": {"path": self.input_audio, "alt_text": "用户输入音频"}})
                if self.input_text:
                    chat_history_state.append({"role": "user", "content": self.input_text})

                # 重置结果字典和输出队列
                self.results = {}
                self.output_queue = queue.Queue()

                submit_btn_state = gr.update(interactive=False, value='AI响应中，请等待')

                # 在开始时，yield 初始状态，保持加载指示器
                # yield [chat_history_state, chat_history_state, submit_btn_state] + [gr.update() for _ in inputs]

                # 在单独的线程中运行核心逻辑函数
                def run_core_logic():
                    self.core_logic()
                    # 在核心逻辑完成后，向队列发送一个结束信号
                    self.output_queue.put(None)

                threading.Thread(target=run_core_logic).start()

                # 不断从队列中获取结果并更新对话历史
                text_flag = False
                while True:
                    item = self.output_queue.get()
                    if item is None:
                        break  # 核心逻辑已完成
                    # 更新 self.results
                    self.results.update(item)
                    # 构建 AI 的回复消息
                    if 'image' in self.results:
                        chat_history_state.append({"role": "assistant", "content": f'![AI图像]({self.results["image"]})'})
                    if 'audio' in self.results:
                        audio_b64 = self.results['audio']
                        chat_history_state.append({"role": "assistant", "content": f'<audio controls autoplay><source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3"></audio>'})
                    if 'text' in self.results:
                        if not text_flag:
                            chat_history_state.append({"role": "assistant", "content": self.results['text']})
                            text_flag = True
                        else:
                            last_content = chat_history_state[-1]['content']
                            if '[AI图像]' not in last_content and '<audio controls autoplay>' not in last_content:
                                chat_history_state[-1]['content'] += self.results['text']
                    yield [chat_history_state, chat_history_state, submit_btn_state] + [gr.update() for _ in inputs]

                # 处理完成后，清除状态文本
                submit_btn_state = gr.update(interactive=True, value="提交")
                yield [chat_history_state, chat_history_state, submit_btn_state] + [gr.update(visible=True, value=None) for _ in inputs]

            submit_button.click(
                fn=gradio_callback,
                inputs=inputs + [state],
                outputs=[chat_history, state, submit_button] + inputs,
                queue=True
            )

        demo.launch(**kwargs)