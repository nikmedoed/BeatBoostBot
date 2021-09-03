import requests
import json
from bot_settings import TARGET_SHEET_URL

def sendData(uid, username, link):
    try:
        data = {
            "userid": uid,
            "nikname": username,
            "link": link
        }
        response = requests.post(TARGET_SHEET_URL, json.dumps(data) )
        return response.json()
    except:
        return {"error": True}


if __name__ == "__main__":
    print(sendData(1111, "dfsdfsdf", "dfsdfsdfsdfdsfsssdzxc"))
