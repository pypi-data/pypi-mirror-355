import os
from flask import Flask, render_template, jsonify, request, url_for, send_from_directory
import base64
import threading
from pathlib import Path
import uuid
import logging
from http import HTTPStatus
import dashscope
import requests
import time
import json
from openai import OpenAI
import tempfile
from PIL import Image  # 引入Pillow库


RESOURCE_PATH = Path(__file__).parent.resolve()

STYLE_TO_PROMPT_SUFFIX = {
    '<3d cartoon>': '3D卡通风格',
    '<anime>': '二次元动漫风格',
    '<oil painting>': '油画风格',
    '<watercolor>': '水彩风格',
    '<flat illustration>': '扁平插画风格',
}


def resolve_resource_path(path):
    """
    解析资源路径：将相对路径与应用的资源路径结合，返回绝对路径。

    参数:
    path (str): 相对资源路径。

    返回:
    Path: 绝对资源路径。
    """
    return Path(RESOURCE_PATH / path).resolve()


# 大模型文字交互
def text_generation(chat_history, prompt='你是一个人工智能助手，你的名字叫小H', stream=False):
    """
    与大模型进行文字交互，基于给定的对话历史和提示进行响应生成。

    参数:
    chat_history (list): 对话历史，每个元素为用户或助手的一条消息。
    prompt (str): 提示文本，用于引导模型的响应，默认为"你是一个人工智能助手，你的名字叫小H"。
    stream (bool): 是否以流式方式获取生成结果，默认为False。

    返回:
    str: 模型生成的响应文本，或错误信息。
    """

    def generator():
        # 生成器，用于流式返回响应
        if AIWebApp.mode == 'openai':
            complete_content = ""  # 用于累积增量内容
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    complete_content += chunk.choices[0].delta.content  # 累积增量内容
                    yield complete_content
        else:
            for r in response:
                if r.status_code == HTTPStatus.OK:
                    yield r.output.choices[0]['message']['content']
                else:
                    return "错误: " + r.message

    try:
        result = words_check(chat_history[-1])
        if result['status'] == 'error':
            return result['message']
        result = words_check(prompt)
        if result['status'] == 'error':
            return result['message']

        messages = [{'role': 'system', 'content': prompt}]
        for index, content in enumerate(chat_history):
            if len(content) != 0:
                if index % 2 == 0:
                    messages.append({'role': 'user', 'content': content})
                else:
                    messages.append({'role': 'assistant', 'content': content})
            else:
                return '输入参数错误'

        if AIWebApp.mode == 'openai':
            response = AIWebApp.client.chat.completions.create(model="qwen-plus",
                                                               messages=messages,
                                                               stream=stream)
        else:
            response = dashscope.Generation.call(model="qwen-plus",
                                                 messages=messages,
                                                 result_format='message',
                                                 stream=stream)
        if stream:
            return generator()
        else:
            if AIWebApp.mode == 'openai':
                return response.choices[0].message.content
            else:
                if response.status_code == HTTPStatus.OK:
                    return response.output.choices[0]['message']['content']
                else:
                    return "错误: " + response.message
    except Exception as e:
        return "错误: " + str(e)


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


# 大模型图像理解
def image_understanding(img, chat_history, prompt='你是一名人工智能助手', stream=False):
    """
    大模型对图像进行理解，基于对话历史和图像进行响应生成。

    参数:
    img (str): 图像的本地路径或URL。
    chat_history (list): 对话历史，每个元素为用户或助手的一条消息。
    prompt (str): 提示文本，用于引导模型的响应，默认为"你是一名人工智能助手"。
    stream (bool): 是否以流式方式获取生成结果，默认为False。

    返回:
    str: 模型生成的响应文本，或错误信息。
    """

    def generator():
        # 生成器，用于流式返回响应
        if AIWebApp.mode == 'openai':
            complete_content = ""  # 用于累积增量内容
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    complete_content += chunk.choices[0].delta.content  # 累积增量内容
                    yield complete_content
        else:
            for r in response:
                if r.status_code == HTTPStatus.OK:
                    yield r.output.choices[0].message.content[0]['text']
                else:
                    return "错误: " + r.message

    try:
        result = words_check(chat_history[-1])
        if result['status'] == 'error':
            return result['message']
        result = words_check(prompt)
        if result['status'] == 'error':
            return result['message']

        if AIWebApp.mode == 'openai':
            base64_image = encode_image(resolve_resource_path(img))
            img_url = f"data:image/jpeg;base64,{base64_image}"
            messages = [{'role': 'system', 'content': [{'type': 'text', 'text': prompt}]},
                        {'role': 'user', 'content': [{'type': 'image_url', 'image_url': {'url': img_url}},
                                                     {'type': 'text', 'text': chat_history[0]}]}]
            for index, content in enumerate(chat_history[1:]):
                if index % 2 == 0:
                    messages.append({'role': 'assistant', 'content': [{'type': 'text', 'text': content}]})
                else:
                    messages.append({'role': 'user', 'content': [{'type': 'text', 'text': content}]})
        else:
            img_url = f"file://{resolve_resource_path(img)}"
            messages = [{'role': 'system', 'content': [{'text': prompt}]},
                        {'role': 'user', 'content': [{'image': img_url}, {'text': chat_history[0]}]}]
            for index, content in enumerate(chat_history[1:]):
                if index % 2 == 0:
                    messages.append({'role': 'assistant', 'content': [{'text': content}]})
                else:
                    messages.append({'role': 'user', 'content': [{'text': content}]})

        if AIWebApp.mode == 'openai':
            response = AIWebApp.client.chat.completions.create(model="qwen-vl-plus",
                                                               messages=messages,
                                                               max_tokens=300,
                                                               stream=stream)
        else:
            response = dashscope.MultiModalConversation.call(model='qwen-vl-plus',
                                                             messages=messages,
                                                             stream=stream)
        if stream:
            return generator()
        else:
            if AIWebApp.mode == 'openai':
                return response.choices[0].message.content
            else:
                if response.status_code == HTTPStatus.OK:
                    return response.output.choices[0].message.content[0]['text']
                else:
                    return "错误: " + response.message
    except Exception as e:
        return "错误: " + str(e)


# 大模型声音理解（新key不支持流式输出）
def audio_understanding(audio, chat_history, prompt='你是一名人工智能助手', stream=False):
    """
    大模型对声音进行理解，基于对话历史和音频进行响应生成。

    参数:
    audio (str): 音频的本地路径或URL。
    chat_history (list): 对话历史，每个元素为用户或助手的一条消息。
    prompt (str): 提示文本，用于引导模型的响应，默认为"你是一名人工智能助手"。
    stream (bool): 是否以流式方式获取生成结果，默认为False。

    返回:
    str: 模型生成的响应文本，或错误信息。
    """

    def generator():
        # 生成器，用于流式返回响应
        complete_content = ""  # 用于累积增量内容
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                complete_content += chunk.choices[0].delta.content  # 累积增量内容
                yield complete_content
    try:
        result = words_check(chat_history[-1])
        if result['status'] == 'error':
            return result['message']
        result = words_check(prompt)
        if result['status'] == 'error':
            return result['message']

        audio_file = resolve_resource_path(audio)
        base64_audio = encode_image(audio_file)
        messages = [{'role': 'system', 'content': [{'type': 'text', 'text': prompt}]},
                    {'role': 'user', 'content': [{'type': 'input_audio',
                                                  'input_audio': {"data": f"data:;base64,{base64_audio}",
                                                                  'format': 'wav'}},
                                                 {'type': 'text', 'text': chat_history[0]}]}]
        for index, content in enumerate(chat_history[1:]):
            if index % 2 == 0:
                messages.append({'role': 'assistant', 'content': [{'type': 'text', 'text': content}]})
            else:
                messages.append({'role': 'user', 'content': [{'type': 'text', 'text': content}]})

        response = AIWebApp.client.chat.completions.create(model="qwen-omni-turbo-latest",
                                                           messages=messages, stream=True)

        if stream:
            return generator()
        else:
            complete_content = ""  # 用于累积增量内容
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    complete_content += chunk.choices[0].delta.content  # 累积增量内容
            return complete_content
    except Exception as e:
        return "错误: " + str(e)


# 大模型图像生成
def image_generation(prompt):
    """
    根据提示文本生成图像。

    参数:
    prompt (str): 提示文本，用于指导图像生成。

    返回:
    str: 生成的图像URL，或错误信息。
    """
    try:
        result = words_check(prompt)
        if result['status'] == 'error':
            return result['message']

        if AIWebApp.mode == 'openai':
            response = AIWebApp.client.images.generate(model="wanx-v1",
                                                       prompt=prompt,
                                                       n=1,
                                                       size="1024x1024")
            return response.data[0].url
        else:
            response = dashscope.ImageSynthesis.async_call(model='wanx-v1',
                                                           prompt=prompt,
                                                           n=1,
                                                           size='1024*1024')
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
def human_repaint(img, style=7):
    """
    使用大模型对人像图片进行风格重绘。

    参数:
    img: 图像文件，本地路径或网络URL。
    style: 风格指数，默认为7。

    返回值:
    重绘后的图像URL或错误信息。
    """
    try:
        if AIWebApp.mode == 'openai':
            response = requests.post(AIWebApp.server_url + '/images/generations/human',
                                     files={'input_img': open(resolve_resource_path(img), 'rb')},
                                     data={'style_index': style, 'model': 'wanx-style-repaint-v1'},
                                     headers={"Authorization": "Bearer " + AIWebApp.api_key},
                                     timeout=30)
            if response.status_code == HTTPStatus.OK:
                return response.json()['data'][0]['url']
            else:
                return "错误: " + response.text
        else:
            img_url = upload_file(img)  # 上传图像文件
            url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation'

            headers = {
                'Content-Type': 'application/json',
                'Authorization': dashscope.api_key,
                'X-DashScope-Async': 'enable',
                'X-DashScope-OssResourceResolve': 'enable'
            }

            params = {
                'model': 'wanx-style-repaint-v1',
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



def resize_image_for_model(
        image_path: str,
        min_dim: int = 512,
        max_dim: int = 4096
) -> str:
    """
    检查并调整图像尺寸以满足模型要求 [min_dim, max_dim]。

    此函数会尽量保持图像的原始长宽比。
    1. 如果图像尺寸已在范围内，直接返回原路径。
    2. 如果超出范围，会进行等比例缩放。
    3. 如果等比例缩放无法满足要求（极端长宽比），则会进行非等比例缩放以确保尺寸合规。

    参数:
    image_path: 本地图像文件的路径。
    min_dim: 尺寸的最小值。
    max_dim: 尺寸的最大值。

    返回值:
    处理后符合要求的图像文件路径。可能是原路径或一个新创建的临时文件路径。
    """
    try:
        img = Image.open(image_path)
        original_width, original_height = img.size

        # 检查是否需要调整
        if (min_dim <= original_width <= max_dim) and \
                (min_dim <= original_height <= max_dim):
            print("图像尺寸已在要求范围内，无需调整。")
            return image_path

        print(f"原始图像尺寸: {original_width}x{original_height}。正在调整以满足 [{min_dim}, {max_dim}] 的要求...")

        # 优先尝试等比例缩放
        w, h = original_width, original_height
        aspect_ratio = w / h

        # 步骤1: 如果任何一边大于max_dim，则等比例缩小
        if w > max_dim or h > max_dim:
            if w > h:
                w = max_dim
                h = int(w / aspect_ratio)
            else:
                h = max_dim
                w = int(h * aspect_ratio)

        # 步骤2: 缩小后，如果任何一边小于min_dim，则等比例放大
        if w < min_dim or h < min_dim:
            if w < h:
                w = min_dim
                h = int(w / aspect_ratio)
            else:
                h = min_dim
                w = int(h * aspect_ratio)

        # 最终检查：如果等比例缩放后的结果仍然超出范围（发生在极端长宽比的情况下）
        # 则回退到强制非等比例缩放，确保尺寸绝对合规
        if not ((min_dim <= w <= max_dim) and (min_dim <= h <= max_dim)):
            print(f"警告: 图像长宽比极端，等比例缩放无法满足所有约束。将进行非等比例缩放。")
            final_width = max(min_dim, min(original_width, max_dim))
            final_height = max(min_dim, min(original_height, max_dim))
        else:
            final_width, final_height = w, h

        final_width = max(1, final_width)  # 确保尺寸不为0
        final_height = max(1, final_height)  # 确保尺寸不为0

        print(f"调整后尺寸: {final_width}x{final_height}")

        # 使用高质量的抗锯齿滤镜进行缩放
        resized_img = img.resize((final_width, final_height), Image.Resampling.LANCZOS)

        # 保存到临时文件
        # 保留原始格式或默认为PNG
        suffix = os.path.splitext(image_path)[1] or '.png'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix="resized_") as tmp:
            resized_img.save(tmp.name)
            return tmp.name

    except Exception as e:
        print(f"错误: 调整图像尺寸时发生异常: {e}")
        # 如果调整失败，则返回原始路径，让API自己处理可能发生的错误
        return image_path


# 涂鸦作画
def sketch_to_image(img, prompt, style='<anime>'):
    """
    将涂鸦图像转换为现实图像。
    此版本会先检查并调整图像尺寸，确保其长宽均在512-4096像素之间。

    参数:
    img: 涂鸦图像文件，本地路径或网络URL。
    prompt: 描述期望图像的文字提示。
    style: 风格标签，默认为'<anime>'。

    返回值:
    生成的图像URL或错误信息。
    """
    img_local_path = None
    resized_img_path = None
    temp_files_to_clean = []

    try:
        # --- 图像预处理 ---
        try:
            # 步骤1: 确保我们有一个本地图像文件路径
            img_local_path = resolve_resource_path(img)
            # 如果resolve_resource_path创建了临时文件，记录下来以便清理
            if img_local_path != img:
                temp_files_to_clean.append(img_local_path)
        except (ValueError, requests.exceptions.RequestException) as e:
            return f"错误: 获取输入图像失败 - {str(e)}"

        # 步骤2: 调整图像尺寸以满足模型要求
        resized_img_path = resize_image_for_model(img_local_path)
        # 如果resize_image_for_model创建了新文件，记录下来以便清理
        if resized_img_path != img_local_path:
            temp_files_to_clean.append(resized_img_path)

        final_image_path = resized_img_path  # 后续流程都使用这个调整后的图像路径

        # --- Prompt处理 ---
        check_result = words_check(prompt if prompt else "")
        if check_result['status'] == 'error':
            return check_result['message']

        current_prompt = prompt if prompt else '根据输入图像的轮廓特征，少量扩充和涂色'
        style_suffix_text = STYLE_TO_PROMPT_SUFFIX.get(style, STYLE_TO_PROMPT_SUFFIX['<anime>'])
        final_prompt_with_style = f"{current_prompt}，{style_suffix_text}"
        if len(final_prompt_with_style) > 800:
            final_prompt_with_style = final_prompt_with_style[:800]

        # --- API调用逻辑 ---
        if AIWebApp.mode == 'openai':
            # OpenAI 代理路径
            input_data_dict = {"function": "doodle", "prompt": final_prompt_with_style}
            parameters_dict = {"n": 1, "is_sketch": True}
            data_payload = {
                "model": "wanx2.1-imageedit",
                "input_data": json.dumps(input_data_dict),
                "parameters": json.dumps(parameters_dict)
            }
            try:
                with open(final_image_path, "rb") as f_img:
                    response = requests.post(
                        AIWebApp.server_url + "/images/generations/graffiti",
                        files={"input_img": f_img},
                        data=data_payload,
                        headers={"Authorization": "Bearer " + AIWebApp.api_key},
                        timeout=60
                    )
                if response.status_code == HTTPStatus.OK:
                    response_json = response.json()
                    if 'data' in response_json and len(response_json['data']) > 0:
                        return response_json['data'][0].get('url', f"错误: 响应中未找到URL - {response.text}")
                    else:
                        return f"错误: 响应格式不正确 - {response.text}"
                else:
                    return f"错误: {response.status_code} - {response.text}"
            except FileNotFoundError:
                return f"错误: 涂鸦图像文件 '{final_image_path}' 未找到。"

        else:
            # Dashscope 原生路径
            img_url = upload_file(final_image_path)
            if not img_url or not img_url.startswith('http'):
                return f"错误: 涂鸦图像上传失败"

            url = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-synthesis/'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {dashscope.api_key}',
                'X-DashScope-Async': 'enable',
            }
            payload = {
                'model': 'wanx2.1-imageedit',
                'input': {
                    'function': 'doodle',
                    'base_image_url': img_url,
                    'prompt': final_prompt_with_style
                },
                'parameters': {'n': 1, 'is_sketch': True}
            }
            response = requests.post(url, headers=headers, json=payload, timeout=30)

            if response.status_code != HTTPStatus.OK:
                return f"错误: {response.status_code} - {response.text}"

            task_id = response.json().get('output', {}).get('task_id')
            if not task_id:
                return f"错误: API响应格式不正确，未找到task_id - {response.text}"

            # 轮询逻辑 (与原版相同)
            max_retries, poll_interval = 20, 3
            for _ in range(max_retries):
                time.sleep(poll_interval)
                task_status_response = requests.get(
                    f'https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}',
                    headers={'Authorization': f'Bearer {dashscope.api_key}'},
                    timeout=30
                )
                if task_status_response.status_code == HTTPStatus.OK:
                    task_data = task_status_response.json()
                    task_output = task_data.get('output', {})
                    task_status = task_output.get('task_status')

                    if task_status == 'SUCCEEDED':
                        results = task_output.get('results')
                        if results and 'url' in results[0]:
                            return results[0]['url']
                        else:
                            return f"错误: 任务成功但结果中未找到URL - {task_status_response.text}"
                    elif task_status == 'FAILED':
                        error_message = task_output.get('message', '未知错误')
                        return f"错误: 任务处理失败 - {error_message} - {task_status_response.text}"
                    elif task_status in ['PENDING', 'RUNNING']:
                        continue
                    else:
                        return f"错误: 未知任务状态 '{task_status}' - {task_status_response.text}"
                else:
                    return f"错误: 查询任务状态失败 {task_status_response.status_code} - {task_status_response.text}"
            return "错误: 任务处理轮询超时。"

    except requests.exceptions.Timeout:
        return "错误: 请求超时。"
    except requests.exceptions.RequestException as e:
        return f"错误: 网络请求异常 - {str(e)}"
    except Exception as e:
        # 捕获所有其他意外错误，包括Pillow可能抛出的错误
        return f"错误: 意外错误 - {str(e)}"
    finally:
        # --- 统一清理临时文件 ---
        for file_path in temp_files_to_clean:
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"已清理临时文件: {file_path}")
            except OSError as e:
                print(f"警告: 清理临时文件 {file_path} 失败: {e}")


# 语音识别
def speech_recognition(audio):
    """
    将语音转换为文字。

    参数:
    audio: 语音文件，本地路径或网络URL。

    返回值:
    识别出的文字或错误信息。
    """
    try:
        if AIWebApp.mode == 'openai':
            audio_file = open(resolve_resource_path(audio), "rb")
            transcript = AIWebApp.client.audio.transcriptions.create(model="paraformer-v2",
                                                                     file=audio_file)
            return transcript.text
        else:
            audio_url = upload_file(audio)  # 上传语音文件
            task_response = dashscope.audio.asr.Transcription.async_call(
                model='paraformer-v2',
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
def speech_synthesis(text, model='sambert-zhiying-v1', rate=1, pitch=1, voice='longxiaochun'):
    """
    将文字转换为语音。

    参数:
    text: 要合成的文字。
    model: 合成语音的模型，默认为'sambert-zhiying-v1'。
    rate: 语速调整，默认为1。
    pitch: 语调调整，默认为1。

    返回值:
    合成的语音文件路径或错误信息。
    """
    try:
        if AIWebApp.mode == 'openai':
            response = AIWebApp.client.audio.speech.create(input=text,
                                                           model='cosyvoice-v1',
                                                           voice=voice)
            filename = f"{uuid.uuid4()}.wav"
            output_file_path = str(resolve_resource_path(f'static/audios/{filename}'))
            response.stream_to_file(output_file_path)
            return f'static/audios/{filename}'
        else:
            result = dashscope.audio.tts.SpeechSynthesizer.call(model=model,
                                                                text=text,
                                                                rate=rate,  # 0.5-2
                                                                pitch=pitch)  # 0.5-2
            if result.get_audio_data() is not None:
                audio_data = result.get_audio_data()
                filename = f"{uuid.uuid4()}.wav"
                output_file_path = str(resolve_resource_path(f'static/audios/{filename}'))
                with open(output_file_path, 'wb') as audio_file:
                    audio_file.write(audio_data)
                return f'static/audios/{filename}'
            else:
                return '错误: ' + result.get_response().message
    except Exception as e:
        return "错误: " + str(e)


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


def words_check(content):
    """
    检查文本中是否含有违禁词。

    参数:
    content: 要检查的文本。

    返回值:
    检查结果，包含状态和消息。
    """
    return {'status': 'success', 'message': ''}
    url = "http://wordscheck.hlqeai.cn/wordscheck"
    data = json.dumps({'content': content})
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=data, headers=headers)
    if response.json()['code'] == '0':
        if response.json()['word_list']:
            return {'status': 'error', 'message': '您的输入信息可能含有违禁词，请谨慎输入'}
        else:
            return {'status': 'success', 'message': ''}
    else:
        return {'status': 'error', 'message': response.json()['msg']}


class AIWebApp:
    """
    一个基于Flask框架的人工智能Web应用程序类。
    """
    server_url = "https://chatapi.hlestudy.com/v1"
    client = OpenAI(base_url=server_url, api_key='')
    mode = 'dashscope'

    def __init__(self, title='My AI Web App'):
        """
        初始化AIWebApp实例。

        :param title: 应用程序的标题，默认为 'My AI Web App'。
        """
        self.app = Flask(__name__)
        # 设置Werkzeug日志记录错误级别
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self.title = title
        self.components = []  # 组件列表
        self.input_pic = None  # 上传的图片路径
        self.input_audio = None  # 上传的音频路径
        self.input_text = ''  # 输入的文本内容
        self.results = []  # 存储处理结果

    @classmethod
    def set_apikey(cls, key):
        """
        设置API密钥。

        :param key: API密钥。
        """
        dashscope.api_key = key
        cls.mode = 'dashscope'
        cls.api_key = key
        cls.client = OpenAI(base_url='https://dashscope.aliyuncs.com/compatible-mode/v1', api_key=key)


    @classmethod
    def set_apikey_new(cls, key):
        cls.api_key = key
        cls.client = OpenAI(base_url=cls.server_url, api_key=key)
        cls.mode = 'openai'

    def add_input_text(self):
        """
        添加文本输入组件到组件列表。
        """
        self.components.append({
            'type': 'input_text',
            'id': 'textComponent'
        })

    def add_camera(self):
        """
        添加摄像头组件到组件列表。
        """
        self.components.append({
            'type': 'camera',
            'id': 'cameraComponent'
        })

    def add_record(self):
        """
        添加录音组件到组件列表。
        """
        self.components.append({
            'type': 'record',
            'id': 'recordComponent'
        })

    def add_pic_file(self):
        """
        添加图片上传组件到组件列表。
        """
        self.components.append({
            'type': 'input_pic',
            'id': 'inputPicComponent'
        })

    def add_audio_file(self):
        """
        添加音频上传组件到组件列表。
        """
        self.components.append({
            'type': 'input_audio',
            'id': 'inputAudioComponent'
        })

    def add_submit(self, callback=None):
        """
        添加提交按钮组件到组件列表，并设置提交时的回调函数。

        :param callback: 提交时的回调函数。
        """
        self.ai_callback = callback
        self.components.append({
            'type': 'submit',
            'id': 'submitButton'
        })

    def setup_routes(self):
        """
        设置应用程序的路由。
        """

        @self.app.route('/')
        def index():
            """
            首页路由，返回索引页面。
            """
            return render_template('index_modern.html', title=self.title)

        @self.app.route('/get_components')
        def get_components():
            """
            返回组件列表的JSON格式。
            """
            return jsonify(self.components)

        @self.app.route('/save_image', methods=['POST'])
        def save_image():
            """
            处理图片上传并保存。
            """
            data = request.get_json()
            image_data = data['image']

            header, encoded = image_data.split(",", 1)
            image_bytes = base64.b64decode(encoded)

            filename = f"{uuid.uuid4()}.png"
            filepath = Path(resolve_resource_path('static/images')) / filename

            with open(filepath, 'wb') as file:
                file.write(image_bytes)

            self.input_pic = str(str(Path('static/images') / filename))
            return jsonify({'filePath': str(filepath)})

        @self.app.route('/save_audio', methods=['POST'])
        def save_audio():
            """
            处理音频上传并保存。
            """
            if 'audioFile' not in request.files:
                return jsonify({'error': 'No audio file part'}), 400
            audio_file = request.files['audioFile']
            if audio_file.filename == '':
                return jsonify({'error': 'No selected audio file'}), 400
            if audio_file:
                filename = f"{uuid.uuid4()}.wav"
                filepath = Path(resolve_resource_path('static/audios')) / filename
                audio_file.save(filepath)
                self.input_audio = str(Path('static/audios') / filename)
                return jsonify({'message': 'Audio file uploaded successfully', 'filePath': str(filepath)})

        @self.app.route('/upload_image', methods=['POST'])
        def upload_image():
            """
            处理外部提交的图片上传。
            """
            if 'file' not in request.files:
                return jsonify({'error': 'No file part'}), 400
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
            if file:
                filename = file.filename
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                filename = f"{uuid.uuid4()}.{ext}"
                file_path = Path(resolve_resource_path('static/images')) / filename
                file.save(file_path)
                self.input_pic = str(Path('static/images') / filename)
                file_url = url_for('static', filename=f'images/{filename}', _external=True)
                return jsonify({'message': 'File uploaded successfully', 'fileUrl': file_url})

        @self.app.route('/upload_audio', methods=['POST'])
        def upload_audio():
            """
            处理外部提交的音频上传。
            """
            if 'file' not in request.files:
                return jsonify({'error': 'No file part'}), 400
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
            if file:
                filename = file.filename
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                filename = f"{uuid.uuid4()}.{ext}"
                file_path = Path(resolve_resource_path('static/audios')) / filename
                file.save(file_path)
                self.input_audio = str(Path('static/audios') / filename)
                file_url = url_for('static', filename=f'audios/{filename}', _external=True)
                return jsonify({'message': 'File uploaded successfully', 'fileUrl': file_url})

        @self.app.route('/submit-text', methods=['POST'])
        def submit_text():
            """
            处理文本提交。
            """
            data = request.get_json()
            self.input_text = data['text']
            return jsonify({'message': '文本内容已成功接收'})

        @self.app.route('/submit', methods=['POST'])
        def submit():
            """
            处理提交按钮点击事件，触发回调函数并返回处理结果。
            """
            threading.Thread(target=self.ai_callback).start()
            response = {"status": "success"}
            if self.input_text:
                response['text'] = self.input_text
            if self.input_pic:
                response['image'] = self.input_pic
            if self.input_audio:
                response['audio'] = self.input_audio
            return jsonify(response)

        @self.app.route('/result', methods=['GET'])
        def get_result():
            """
            获取处理结果。
            """
            if self.results:
                new_result = self.results.pop()
                self.results.clear()
                if 'running' in new_result:
                    new_result['status'] = 'processing'
                else:
                    new_result['status'] = 'finish'
                return jsonify(new_result)
            return jsonify({"status": "processing", "content": ""})

        @self.app.route('/static/audios/<filename>')
        def audio_file(filename):
            """
            服务静态音频文件。
            """
            return send_from_directory('static/audios', filename)

        @self.app.route('/static/images/<filename>')
        def image_file(filename):
            """
            服务静态图片文件。
            """
            return send_from_directory('static/images', filename)

    def run(self, **kwargs):
        """
        运行应用程序。

        :param kwargs: 可变参数，可用于指定运行参数，如端口号。
        """
        # 确保静态文件目录存在
        if not os.path.exists(resolve_resource_path('static/images')):
            os.mkdir(resolve_resource_path('static/images'))
        if not os.path.exists(resolve_resource_path('static/audios')):
            os.mkdir(resolve_resource_path('static/audios'))
        # 清理旧的静态文件
        for file in os.listdir(resolve_resource_path('static/images')):
            os.remove(os.path.join(resolve_resource_path('static/images'), file))
        for file in os.listdir(resolve_resource_path('static/audios')):
            os.remove(os.path.join(resolve_resource_path('static/audios'), file))
        self.setup_routes()
        # 启动Flask应用
        if 'port' in kwargs:
            port = kwargs['port']
        else:
            port = '5000'
        print(f'访问地址：http://127.0.0.1:{port}')
        self.app.run(**kwargs)
