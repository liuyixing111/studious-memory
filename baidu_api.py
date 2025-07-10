import requests

API_KEY = "rqRBT1i54kqNALhcmuWbGjXw"
SECRET_KEY = "Sqsi0Eg1AvxPq2uP2yqC88x9Lap7X6JK"


def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))

def chatbaidu(conversation_list):
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant?access_token=" + get_access_token()
    headers = {
            'Content-Type': 'application/json'
        }
    data  = {
        "messages": conversation_list
        }
    res = requests.request("POST", url, headers=headers, json=data).json()
    answer = res['result']
    print(answer)
    return answer

#chatbaidu([{"role": "user", "content": "how about suzhou weather"}])