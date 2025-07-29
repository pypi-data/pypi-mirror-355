from flask import Flask, request, jsonify
import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider
import os

app = Flask(__name__)

# 初始化OSS客户端
# 确保环境变量 OSS_ACCESS_KEY_ID 和 OSS_ACCESS_KEY_SECRET 已设置
auth = oss2.ProviderAuth(EnvironmentVariableCredentialsProvider())
# 替换为你的OSS Endpoint和Bucket名称
bucket = oss2.Bucket(auth, 'https://oss-cn-hangzhou.aliyuncs.com', 'temp-file-oss')


# 上传文件的函数
def upload_file_to_oss(file, filename):
    try:
        # 将文件内容传输到OSS
        bucket.put_object(filename, file.read())
        # 返回文件的URL
        url = f"https://temp-file-oss.oss-cn-hangzhou.aliyuncs.com/{filename}"
        return url
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None


@app.route('/upload', methods=['POST'])
def upload_file():
    # 检查是否有文件在请求中
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    # 如果用户未选择文件
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # 使用原文件名或可自定义处理逻辑生成文件名
    filename = file.filename

    # 上传文件至OSS
    url = upload_file_to_oss(file, filename)
    if url:
        return jsonify({"url": url}), 200
    else:
        return jsonify({"error": "File upload failed"}), 500


if __name__ == '__main__':
    # 设置debug模式
    app.run(host='0.0.0.0', port=6500)
