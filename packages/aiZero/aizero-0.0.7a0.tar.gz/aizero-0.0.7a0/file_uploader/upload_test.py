import requests

# 上传文件的 Flask 服务的 URL
upload_url = 'http://47.99.81.126:6500/upload'  # 根据你的 Flask 服务地址替换

# 本地文件路径
file_path = '3057c25f-e3ad-4bfd-a499-47785b93ca9f.png'  # 替换为你本地文件的路径

# 打开文件并上传
with open(file_path, 'rb') as file:
    files = {'file': file}
    try:
        response = requests.post(upload_url, files=files)
        # 检查请求是否成功
        if response.status_code == 200:
            data = response.json()
            print(f"File uploaded successfully! File URL: {data['url']}")
        else:
            print(f"Failed to upload file. Server response: {response.json()}")
    except Exception as e:
        print(f"An error occurred: {e}")
