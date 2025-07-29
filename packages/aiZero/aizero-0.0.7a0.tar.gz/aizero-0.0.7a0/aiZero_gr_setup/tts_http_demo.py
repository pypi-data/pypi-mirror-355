#coding=utf-8

'''
requires Python 3.6 or later
pip install requests
'''
import base64
import json
import uuid
import requests


if __name__ == '__main__':
    import gradio as gr


    def my_voice(text):
        # 填写平台申请的appid, access_token以及cluster
        appid = "7222007657"
        access_token = "HBtoifeLx31lJXJj37KOaHaAUu7NwBSm"
        cluster = "volcano_icl"

        voice_type = "S_n7HmK3Ha1"
        host = "openspeech.bytedance.com"
        api_url = f"https://{host}/api/v1/tts"

        header = {"Authorization": f"Bearer;{access_token}"}

        request_json = {
            "app": {
                "appid": appid,
                "token": 'access_token',
                "cluster": cluster
            },
            "user": {
                "uid": "388808087185088"
            },
            "audio": {
                "voice_type": voice_type,
                "encoding": "mp3",
                "speed_ratio": 0.8,
                "volume_ratio": 1.0,
                "pitch_ratio": 1.0,
            },
            "request": {
                "reqid": str(uuid.uuid4()),
                "text": text,
                "text_type": "plain",
                "operation": "query",
                "with_frontend": 1,
                "frontend_type": "unitTson"

            }
        }
        resp = requests.post(api_url, json.dumps(request_json), headers=header)
        if "data" in resp.json():
            data = resp.json()["data"]
            file_to_save = open("test_submit.mp3", "wb")
            file_to_save.write(base64.b64decode(data))
        return "test_submit.mp3"


    demo = gr.Interface(
        fn=my_voice,
        inputs=["text"],
        outputs=["audio"],
        title="emhang的声音合成器",
        flagging_mode="never"
    )

    demo.launch(share=True)

