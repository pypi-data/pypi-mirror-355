import serial
import time
import google.generativeai as genai
from aiZero_gr import AIWebApp, speech_recognition
import pathlib

# 初始化串口
SERIAL_PORT = '/dev/tty.usbserial-53230113071'  # 替换为实际串口名称
BAUD_RATE = 115200
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

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

# 功能函数
def set_light_values(r1: int, g1: int, b1: int, r2: int, g2: int, b2: int, r3: int, g3: int, b3: int):
    """设置三盏组合rgb灯的颜色数值，1～3三盏灯从左至右排列。

    Args:
        r1: 第一盏灯的r数值（0-255）
        g1: 第一盏灯的g数值（0-255）
        b1: 第一盏灯的b数值（0-255）
        r2: 第二盏灯的r数值（0-255）
        g2: 第二盏灯的g数值（0-255）
        b2: 第二盏灯的b数值（0-255）
        r3: 第三盏灯的r数值（0-255）
        g3: 第三盏灯的g数值（0-255）
        b3: 第三盏灯的b数值（0-255）
    """
    code = f"""
    from mpython import *
rgb[0] = ({int(r1)}, {int(g1)}, {int(b1)})
rgb[1] = ({int(r2)}, {int(g2)}, {int(b2)})
rgb[2] = ({int(r3)}, {int(g3)}, {int(b3)})
rgb.write()
    """
    send_to_esp32(code)
    print((r1, g1, b1), (r2, g2, b2), (r3, g3, b3))


def my_ai_function():
    text = app.input_text
    audio = app.input_audio
    if audio is None:
        response = chat.send_message(text)
        app.send(response.text)
    else:
        text = speech_recognition(audio)
        response = chat.send_message(text)
        app.send(response.text)


app = AIWebApp(title='智能家居——AI灯光控制系统')
app.set_apikey('sk-5647aa1303594b73ab6cf9838bfef0d7')
genai.configure(api_key='AIzaSyC20NIv6XNIUArcLVwr69j_xsnsU-WyC-A', transport='rest')
model = genai.GenerativeModel(model_name="gemini-1.5-flash", tools=[set_light_values])
chat = model.start_chat(enable_automatic_function_calling=True)
app.add_input_text()
app.add_input_audio()
app.set_submit(my_ai_function)
app.run()
