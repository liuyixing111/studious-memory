import sys
import subprocess
import pyaudio
import wave
import openai
import signal
from tts import text2voice
import requests
import json
from aip import AipSpeech

MAX_CONVERSATION= 3 #对话轮数

""" 你的 BAIDU APPID AK SK """
BD_APP_ID = '60211397'
BD_API_KEY = 'bjxFoIKaYnbt05TrmhX0y7be'
BD_SECRET_KEY = 'rXztempKvwMa17YG6Z2NUfLM1kBdvZHn'

interrupted = False


def signal_handler(signal, frame):
    global interrupted
    interrupted = True

def interrupt_callback():
    global interrupted
    return interrupted



def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        return fp.read()

def voice2Text():
    #根据语音调用百度的API获取文字
    client = AipSpeech(BD_APP_ID, BD_API_KEY, BD_SECRET_KEY)
    response = client.asr(get_file_content(FINAL_OUTPUT_FILENAME), 'pcm', 16000, {'dev_pid': 1536, })
    print(response)
    
    result = response['result'][0]
    print(result)
    return result

def chatGPT(conversation_list):
    headers = {
        "Authorization": "Bearer "+openai.api_key,
        "Content-Type": "application/json"
    }
    data = {
        "messages": conversation_list,
        "model": "gpt-3.5-turbo"
    }

    response = requests.post("https://oa.api2d.net/v1/chat/completions", headers=headers, json=data)
    completion = response.json()
    print(completion)
    answer = completion["choices"][0]["message"]["content"]
    return answer


def chatbaidu(conversation_list):
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant?access_token=" + get_access_token()
    headers = {
            'Content-Type': 'application/json'
        }
    data  = {
        "messages": conversation_list
        }
    res = requests.request("POST", url, headers=headers, json=data).json()
    print(res)
    answer = res['result']
    print(answer)
    return answer



def play(save_file):
    command = [
        "aplay",
        save_file
    ]

    # 运行命令行
    subprocess.run(command, check=True)

def deleteAudio(save_file):
    command = [
        "rm",
        WAVE_OUTPUT_FILENAME,
        FINAL_OUTPUT_FILENAME,
        save_file
    ]
    subprocess.run(command, check=True)

def show_conversation(conversation_list):
    for msg in conversation_list:
        if msg['role'] == 'user':
            print(f"\U0001f47b: {msg['content']}\n")
        else:
            print(f"\U0001f47D: {msg['content']}\n")

def chat_bot_main(duration,conversation_list = []):
    record_seconds=duration
    mic(record_seconds)
    changeRate()
    question=voice2Text()
    if "开灯" in question:
        print("openlight")
        send_mqtt_message("fang", "1")
        save_file=text2voice("好的，已经帮您开灯")
        play(save_file)
    elif "关灯" in question:
        print("closelight")
        send_mqtt_message("fang", "2")
        save_file=text2voice("好的，已经帮您关灯")
        play(save_file)
    elif "打开风扇" in question:
        print("openfan")
        send_mqtt_message("fang", "3")
        save_file=text2voice("好的，已经帮您打开风扇")
        play(save_file)
    elif "关闭风扇" in question:
        print("closefan")
        send_mqtt_message("fang", "4")
        save_file=text2voice("好的，已经帮您关闭风扇")
        play(save_file)       
    else:    
        conversation_list.append({"role":"user","content":question})
        answer=chatbaidu(conversation_list)
        #print(answer)
        conversation_list.append({"role": "assistant", "content": answer})
        show_conversation(conversation_list)
        save_file=text2voice(answer)
        play(save_file)
        deleteAudio(save_file)
        if len(conversation_list) > 2 * MAX_CONVERSATION:
            # 删除前两个元素
            del conversation_list[:2]
            # 添加两个新元素

if __name__ == '__main__':
    opt, args = options_func()
    signal.signal(signal.SIGINT, signal_handler)
    print('Listening... Press Ctrl+C to exit')
    conversation_list = [{"role": "user", "content": "你叫如影可移动机器人"},{"role": "assistant", "content": "好的我知道了"}]
    #conversation_list = [] #无预设
    #conversation_list = [{"role": "system",
     #                     "content": "你现在正在扮演我的助理,请你表现的活跃友善。"}]
    while (not interrupted):
        detector = snowboydecoder.HotwordDetector(opt.model, sensitivity=0.5)

        def detected_callback():
            """ start chatpi service"""
            # detector.terminate()
            # chatbot.chat_bot_main()
            play("snowboy/resources/ding.wav")
            print("---------start ChatPi---------")
            detector.terminate()
            chat_bot_main(opt.duration,conversation_list)
        detector.start(detected_callback, interrupt_check=interrupt_callback,
                       sleep_time=0.03)
        detector.terminate()




