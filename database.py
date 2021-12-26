import requests
import json


def sendData(TARGET_SHEET_URL, uid, username, link, chatid, chattitle=""):
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
        #TODO на асинхрон перевести
        response = requests.post(TARGET_SHEET_URL, json.dumps(data))
        return response.json()
    except:
        return {"error": "Внутренняя ошибка бота"}


def verificateId(TILDA_SHEET_URL, id):
    try:
        data = {"id": id}
        # TODO на асинхрон перевести
        response = requests.post(TILDA_SHEET_URL, json.dumps(data))
        return response.json()
    except:
        return {"error": True}


if __name__ == "__main__":
    print(sendData(1111, "dfsdfsdf", "dfsdfsdfsdfdsfsssdzxc", 11, "hfuyfuyuyf"))
