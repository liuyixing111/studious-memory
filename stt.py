from aip import AipSpeech


BD_APP_ID = '60211397'
BD_API_KEY = 'bjxFoIKaYnbt05TrmhX0y7be'
BD_SECRET_KEY = 'rXztempKvwMa17YG6Z2NUfLM1kBdvZHn'


def get_file_content(filePath):
    with open(filePath, 'rb') as fp:
        return fp.read()


def voice2Text():
    try:
        #根据语音调用百度的API获取文字
        client = AipSpeech(BD_APP_ID, BD_API_KEY, BD_SECRET_KEY)
        response = client.asr(get_file_content("test.wav"), 'pcm', 16000, {'dev_pid': 1537, })
        print(response)
        result = response['result'][0]
        print(result)
        return result
    except ZeroDivisionError as e:
        return e
