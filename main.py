import pyaudio
import wave
import threading
import time
import os
import serial
from stt import voice2Text
from tts import text2voice
from vad import listen
from baidu_api import chatbaidu

# ======== 配置区 ========
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200
TRACKS = ['music1.wav', 'music2.wav', 'music3.wav']
CHUNK_SIZE = 1024  # 音频流块大小
conversation_list = []
# =======================

# 校验音频文件存在
for track in TRACKS:
    if not os.path.exists(track):
        raise FileNotFoundError(f"音频文件 {track} 不存在")

# 预加载音频数据到内存
audio_library = []
for track in TRACKS:
    with wave.open(track, 'rb') as wf:
        params = wf.getparams()
        raw_data = wf.readframes(wf.getnframes())
        audio_library.append({
            'params': params,
            'data': raw_data,
            'name': os.path.basename(track)
        })

# 全局状态管理
playback_control = {
    'current_track': 0,
    'position': 0,
    'paused': False,
    'stop_flag': threading.Event(),
    'player_thread': None,
    'audio_interface': pyaudio.PyAudio()
}

def stream_audio():
    """音频流输出核心函数"""
    track_data = audio_library[playback_control['current_track']]
    print(f"▶ 开始播放：{track_data['name']}")
    
    stream = playback_control['audio_interface'].open(
        format=playback_control['audio_interface'].get_format_from_width(
            track_data['params'][1]),
        channels=track_data['params'][0],
        rate=track_data['params'][2],
        output=True
    )
    
    data_ptr = playback_control['position']
    audio_data = track_data['data']
    
    while data_ptr < len(audio_data) and not playback_control['stop_flag'].is_set():
        if not playback_control['paused']:
            chunk = audio_data[data_ptr:data_ptr+CHUNK_SIZE]
            stream.write(chunk)
            data_ptr += len(chunk)
            playback_control['position'] = data_ptr
        else:
            time.sleep(0.1)
    
    stream.stop_stream()
    stream.close()
    
    # 自然播放结束处理
    if data_ptr >= len(audio_data):
        playback_control['position'] = 0
        playback_control['paused'] = False
        print(f"■ 播放完成：{track_data['name']}")

def show_conversation(conversation_list):
    for msg in conversation_list:
        if msg['role'] == 'user':
            print(f"\U0001f47b: {msg['content']}\n")
        else:
            print(f"\U0001f47D: {msg['content']}\n")

def execute_command(cmd):
    """处理串口命令"""
    cmd = cmd.lower()
    
    if cmd == 'b':  # 播放/恢复
        if playback_control['paused']:
            playback_control['paused'] = False
            print("⏸ 恢复播放")
        else:
            if playback_control['player_thread'] and playback_control['player_thread'].is_alive():
                return
            playback_control['stop_flag'].clear()
            playback_control['player_thread'] = threading.Thread(target=stream_audio)
            playback_control['player_thread'].start()
            
    elif cmd == 's':  # 停止
        playback_control['stop_flag'].set()
        playback_control['paused'] = False
        playback_control['position'] = 0
        print("⏹ 停止播放")
        
    elif cmd == 'p':  # 上一曲
        playback_control['stop_flag'].set()
        if playback_control['player_thread'] and playback_control['player_thread'].is_alive():
            playback_control['player_thread'].join()
        playback_control['current_track'] = (playback_control['current_track'] - 1) % len(TRACKS)
        playback_control['position'] = 0
        playback_control['stop_flag'].clear()
        playback_control['player_thread'] = threading.Thread(target=stream_audio)
        playback_control['player_thread'].start()
        
    elif cmd == 'n':  # 下一曲
        playback_control['stop_flag'].set()
        if playback_control['player_thread'] and playback_control['player_thread'].is_alive():
            playback_control['player_thread'].join()
        playback_control['current_track'] = (playback_control['current_track'] + 1) % len(TRACKS)
        playback_control['position'] = 0
        playback_control['stop_flag'].clear()
        playback_control['player_thread'] = threading.Thread(target=stream_audio)
        playback_control['player_thread'].start()
        
    elif cmd == 'h':  # 暂停并打印
        playback_control['paused'] = True
        print("⏸ 暂停播放")
        listen()
        question = voice2Text()
        conversation_list.append({"role":"user","content":question})
        answer=chatbaidu(conversation_list)
        conversation_list.append({"role": "assistant", "content": answer})
        show_conversation(conversation_list)
        save_file = text2voice(answer)
        #
        if len(conversation_list) > 2 * MAX_CONVERSATION:
            # 删除前两个元素
            del conversation_list[:2]
        
        
        

def serial_monitor():
    """串口监听循环"""
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
        while True:
            if ser.in_waiting:
                cmd = ser.read().decode().strip()
                if cmd in ['b', 's', 'p', 'n', 'h']:
                    execute_command(cmd)

if __name__ == "__main__":
    try:
        print("=== 音乐播放器已启动 ===")
        print("可用命令：b=播放/恢复, s=停止, p=上一曲, n=下一曲, h=暂停+hello")
        serial_monitor()
    finally:
        playback_control['audio_interface'].terminate()