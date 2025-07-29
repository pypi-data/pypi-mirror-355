import serial
import time
from aiZero_gr import AIWebApp, speech_recognition, text_generation
import json
import subprocess
from threading import Thread

# 初始化串口
SERIAL_PORT = '/dev/tty.usbserial-53230113071'  # 替换为实际串口名称
BAUD_RATE = 115200
# ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

def send_to_esp32(command):
    """
    向 ESP32 发送 Python 指令
    Args:
        command (str): 要执行的 Python 代码
    """
    for line in command.strip().split('\n'):
        ser.write((line + '\r\n').encode())  # 按行发送代码
        time.sleep(0.1)  # 每行发送后稍作延时
        print(f"Sent: {line}")
    response = ser.read_all().decode('utf-8')
    print(f"ESP32 Response: {response}")


def run_ampy_command(command):
    """
    执行 ampy 命令
    """
    try:
        result = subprocess.run(
            command, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode == 0:
            print(f"Command succeeded: {result.stdout.strip()}")
        else:
            print(f"Command failed: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def upload_file(local_file, remote_file="main.py"):
    """
    上传文件到 ESP32
    """
    command = f"ampy --port {SERIAL_PORT} --baud {BAUD_RATE} put {local_file} {remote_file}"
    print(f"Uploading {local_file} to {remote_file}...")
    return run_ampy_command(command)

def list_files():
    """
    列出 ESP32 上的文件
    """
    command = f"ampy --port {SERIAL_PORT} --baud {BAUD_RATE} ls"
    print("Listing files on ESP32...")
    return run_ampy_command(command)

def run_file(remote_file="main.py"):
    """
    在 ESP32 上运行文件
    """
    command = f"ampy --port {SERIAL_PORT} --baud {BAUD_RATE} run {remote_file}"
    print(f"Running {remote_file} on ESP32...")
    return run_ampy_command(command)

def run_code():
    upload_file("main.py")
    run_file()


def my_ai_function():
    text = app.input_text
    audio = app.input_audio
    if audio:
        text = speech_recognition(audio)
    response = text_generation(text, history, prompt=prompt_2)
    history.add_ai_content(response)
    # try:
    #     result = json.loads(response)
    #     if len(result) > 1:
    #         code = f'from mpython import *\n'
    #         for n in '123':
    #             if n in result:
    #                 r, g, b = result[n]
    #                 code += f'rgb[{int(n) - 1}] = ({int(r)}, {int(g)}, {int(b)})\n'
    #         code += 'rgb.write()\n'
    #         send_to_esp32(code)
    #     app.send(result['text'])
    # except:
    #     app.send(response)
    try:
        result = json.loads(response)
        if 'code' in result:
            with open('main.py', 'w') as fp:
                fp.write(result['code'])
            Thread(target=run_code).start()
        app.send(result['text'])
    except Exception as e:
        print(str(e))
        app.send(response)


prompt = """请充当一个智能家居控制器，你将能够控制从左至右三盏RGB灯的颜色。请在理解用户指令意思的前提下输出标准的json格式数据，
用1、2、3三个键对应三个颜色数组，例如(255, 0, 0)，每个数组都由R/G/B三原色色值组成，数值都是0-255之间的整数。
最后，用"text"键展示你对用户的反馈文字。
请注意，若你不能有效理解用户的意思，请仍然输出json数据，但不要加入1、2、3这三个键，仅在"text"键中表达对用户的提示。
"""

prompt_2 = """请充当一个智能家居控制器，你将能够运用micropython代码控制三盏RGB灯的颜色。
这个代码始终用from mpython import *的语句完成导入，并可以用如下语句控制某一盏灯颜色：
rgb[0] = (255, 0, 0)
三盏灯从左至右的索引是0、1、2，颜色使用RGB三原色表示，数值范围0-255。
此外，你还可以用如rgb.fill((0, 0, 0))的语句一次性设置所有灯为相同颜色。
颜色设置后，必须用rgb.write()语句才能生效。

请根据上述编程指南，在理解用户指令意思的前提下输出标准的json格式数据（仅包含数据内容，不要用markdown语法标记），
用"code"键对应完整的控制代码内容，用"text"键展示你对用户的反馈文字。
请注意，若你不能有效理解用户的意思，请仍然输出json数据，但不要加入"code"键，仅在"text"键中表达对用户的提示。"""


app = AIWebApp(title='智能家居——AI灯光控制系统')
app.set_apikey('sk-5647aa1303594b73ab6cf9838bfef0d7')
history = app.create_history()
app.add_input_text()
app.add_input_audio()
app.set_submit(my_ai_function)
app.run()
