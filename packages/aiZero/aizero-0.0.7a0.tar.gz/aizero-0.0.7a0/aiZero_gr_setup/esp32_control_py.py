import subprocess

# 配置串口和波特率
SERIAL_PORT = '/dev/tty.usbserial-53230113071'  # 替换为实际的串口名称
BAUD_RATE = 115200

# 本地代码文件路径
LOCAL_FILE = "main.py"


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


def delete_file(remote_file):
    """
    删除 ESP32 上的文件
    """
    command = f"ampy --port {SERIAL_PORT} --baud {BAUD_RATE} rm {remote_file}"
    print(f"Deleting {remote_file} on ESP32...")
    return run_ampy_command(command)


if __name__ == "__main__":
    # 上传文件
    if upload_file(LOCAL_FILE):
        print("File uploaded successfully!")

    # 列出文件
    if list_files():
        print("File listing completed!")

    # 执行文件
    if run_file("main.py"):
        print("File executed successfully!")
