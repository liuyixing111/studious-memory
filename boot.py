import pyaudio
import wave
import threading
import time
import os
import serial
from stt import voice2Text
from tts import text2voice
from micre import listen
from baidu_api import chatbaidu
# ======== 配置区 ========
SERIAL_PORT = '/dev/ttyUSB0'
BAUD_RATE = 115200
TRACKS = ['music1.wav', 'music2.wav', 'music3.wav']
CHUNK_SIZE = 1024
MAX_CONVERSATION = 5  # 最大对话轮次
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
    'voice_stop_flag': threading.Event(),  # 新增语音播放停止标志
    'voice_thread': None,                # 语音播放线程
    'audio_interface': pyaudio.PyAudio(),
    'current_mode': 'music'              # 当前播放模式：music/voice
}

def stream_audio():
    """音乐播放核心函数"""
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
    
    if data_ptr >= len(audio_data):
        playback_control['position'] = 0
        playback_control['paused'] = False
        print(f"■ 播放完成：{track_data['name']}")

def play_voice_response(filename):
    """语音回复播放函数"""
    try:
        with wave.open(filename, 'rb') as wf:
            params = wf.getparams()
            data = wf.readframes(wf.getnframes())
            
        p = pyaudio.PyAudio()
        stream = p.open(
            format=p.get_format_from_width(params[1]),
            channels=params[0],
            rate=params[2],
            output=True
        )
        
        print("▶ 开始播放语音回复")
        position = 0
        while position < len(data) and not playback_control['voice_stop_flag'].is_set():
            chunk = data[position:position+CHUNK_SIZE]
            stream.write(chunk)
            position += len(chunk)
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("■ 语音播放完成")
        
    except Exception as e:
        print(f"语音播放失败：{str(e)}")

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
        
# 修改execute_command的h命令处理部分
    elif cmd == 'h':
        if playback_control['current_mode'] == 'music':
            # 暂停音乐进入语音模式
            playback_control['paused'] = True
            playback_control['stop_flag'].set()
            print("⏸ 音乐暂停，进入语音模式")
            
            # 启动语音交互
            listen(5)
            question = voice2Text()

            # 正常对话流程
            conversation_list.append({"role":"user","content":question})
            answer=chatbaidu(conversation_list)
            conversation_list.append({"role": "assistant", "content": answer})
            show_conversation(conversation_list)
            save_file = text2voice(answer)
            
            # 清理历史对话
            if len(conversation_list) > 2 * MAX_CONVERSATION:
                del conversation_list[:2]
            
            # 启动语音播放（简化版）
            def play_once():
                try:
                    playback_control['current_mode'] = 'voice'
                    with wave.open(save_file, 'rb') as wf:
                        p = pyaudio.PyAudio()
                        stream = p.open(
                            format=p.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True
                        )
                        data = wf.readframes(CHUNK_SIZE)
                        while data and not playback_control['voice_stop_flag'].is_set():
                            stream.write(data)
                            data = wf.readframes(CHUNK_SIZE)
                        stream.stop_stream()
                        stream.close()
                        p.terminate()
                except Exception as e:
                    print(f"语音播放异常: {e}")
                finally:
                    playback_control['current_mode'] = 'music'
                    playback_control['paused'] = False
                    playback_control['stop_flag'].clear()

            playback_control['voice_stop_flag'].clear()
            playback_control['voice_thread'] = threading.Thread(target=play_once)
            playback_control['voice_thread'].start()
            
        elif playback_control['current_mode'] == 'voice':
            # 打断语音播放
            print("⏹ 打断语音播放")
            playback_control['voice_stop_flag'].set()
            if playback_control['voice_thread'] and playback_control['voice_thread'].is_alive():
                playback_control['voice_thread'].join(timeout=0.5)
            
            # 立即恢复音乐播放
            playback_control['current_mode'] = 'music'
            playback_control['paused'] = False
            playback_control['stop_flag'].clear()

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
        print("=== 智能音乐播放器已启动 ===")
        print("可用命令：b=播放/恢复, s=停止, p=上一曲, n=下一曲, h=语音交互")
        serial_monitor()
    finally:
        playback_control['audio_interface'].terminate()
        playback_control['voice_stop_flag'].set()