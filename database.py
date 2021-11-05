import requests
import json
from bot_settings import TARGET_SHEET_URL, TILDA_SHEET_URL


def sendData(uid, username, link, chatid, chattitle=""):
    try:
        data = {
            "setLink": {
                "userid": uid,
                "nikname": username,
                "link": link,
                "chatid": chatid,
                "chattitle": chattitle,
            }
        }
        response = requests.post(TARGET_SHEET_URL, json.dumps(data))
        return response.json()
    except:
        return {"error": "Внутренняя ошибка бота"}



def verificateId(id):
    try:
        data = {"id": id}
        response = requests.post(TILDA_SHEET_URL, json.dumps(data))
        return response.json()
    except:
        return {"error": True}


if __name__ == "__main__":
    print(sendData(1111, "dfsdfsdf", "dfsdfsdfsdfdsfsssdzxc", 11, "hfuyfuyuyf"))
