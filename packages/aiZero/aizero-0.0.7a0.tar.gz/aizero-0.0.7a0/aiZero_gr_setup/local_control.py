import pyautogui
import google.generativeai as genai
from time import sleep

def capture_screen():
    """截屏并返回PIL图像对象"""
    screenshot = pyautogui.screenshot().resize((960, 540))
    # screenshot.show()
    return screenshot

def move_and_click(ymin: int, xmin: int, ymax: int, xmax: int, width: int, height: int):
    """设置鼠标移动到某处并单击。

    Args:
        ymin: 目标位置边界框的ymin数值
        xmin: 目标位置边界框的xmin数值
        ymax: 目标位置边界框的ymax数值
        xmax: 目标位置边界框的xmax数值
        screen_width: 屏幕的宽度
        screen_height: 屏幕的高度
    """
    x = (xmin + xmax) * width / 1000
    y = (ymin + ymax) * height / 1000
    print(x, y)
    pyautogui.moveTo(x, y)
    sleep(1)
    pyautogui.click()
    sleep(1)
    pyautogui.click()


def move_and_send(ymin: int, xmin: int, ymax: int, xmax: int, width: int, height: int, text: str):
    """设置鼠标移动到某个消息框的位置，单击后输入文本消息内容并发送。

    Args:
        ymin: 目标位置边界框的ymin数值
        xmin: 目标位置边界框的xmin数值
        ymax: 目标位置边界框的ymax数值
        xmax: 目标位置边界框的xmax数值
        screen_width: 屏幕的宽度
        screen_height: 屏幕的高度
        text: 需发送的文本内容
    """
    x = (xmin + xmax) * width / 1000
    y = (ymin + ymax) * height / 1000
    print(x, y)
    pyautogui.moveTo(x, y)
    sleep(1)
    pyautogui.click()
    sleep(1)
    pyautogui.click()
    pyautogui.write(text, interval=0.1)
    sleep(1)
    pyautogui.press("enter")

def end_task():
    """表示任务执行完毕"""
    pass


prompt = """
你将根据用户指令尝试对电脑进行操作，你可以调用以下函数：
- capture_screen：获取屏幕截图
- move_and_click: 接收ymin/xmin/ymax/xmin四个表示目标位置边界框数值的参数，以及width/height两个表示屏幕实际尺寸的参数，执行移动鼠标并单击
- move_and_send: 接收ymin/xmin/ymax/xmin四个表示目标位置边界框数值的参数，width/height两个表示屏幕实际尺寸的参数，以及text参数，执行移动鼠标单击消息框，输入text的文本内容并发送
- end_task: 当任务执行完毕或无法继续时调用

你每次接收到用户命令后，都将尝试分步执行，例如，如果用户要求"找到xxx并发送你好"，你应该按下面的步骤执行：
1. 执行屏幕截图
2. 根据用户提供的截图内容判断xxx是否在屏幕上，如果是，确认其在屏幕上的边界框坐标并传递给move_and_click函数
3. 执行屏幕截图
4. 根据用户提供的截图内容判断是否执行成功，若成功，确认消息框在屏幕上的边界框坐标并传递给move_and_send函数，否则返回第2步
5. 执行屏幕截图
6. 根据用户提供的截图内容判断是否执行成功，若成功，给出执行成功反馈，否则返回第4步。

你将根据历史对话记录，仅给出下一步的指令信息并执行函数调用。用户将自动根据反馈给予你下一步所需的数据，直到任务完成。
请注意，一旦你的任务执行结束或到某一步无法继续，请执行对end_task函数的调用。
"""

genai.configure(api_key='AIzaSyC20NIv6XNIUArcLVwr69j_xsnsU-WyC-A', transport='rest')
model = genai.GenerativeModel(model_name="gemini-1.5-pro", system_instruction=prompt,
                              tools=[capture_screen, move_and_click, move_and_send, end_task])
chat = model.start_chat()
running = True
response = chat.send_message("在飞书找到薛冠文，告诉他：你好，我找到你了 by Gemini")

while running:
    print(response)
    for part in response.parts:
        if fn := part.function_call:
            args = ", ".join(
                f"{key}='{val}'" if isinstance(val, str) else f"{key}={val}" for key, val in fn.args.items())
            if fn.name == "capture_screen":
                screen = eval(f"{fn.name}({args})")
                sleep(1)
                response = chat.send_message([f"已截图，屏幕大小是{screen.size}", screen])
            elif fn.name == "end_task":
                running = False
            else:
                exec(f"{fn.name}({args})")
                sleep(1)
                response = chat.send_message("已执行操作，请进行下一步")
            break
