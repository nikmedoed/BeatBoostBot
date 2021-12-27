import requests
import json
import aiohttp


async def send_linkdata_to_sheet(TARGET_SHEET_URL, uid, username, link, chatid, chattitle=""):
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
        async with aiohttp.ClientSession() as session:
            async with session.post(TARGET_SHEET_URL, json=data) as resp:  # [1]
                return await resp.json()
    except:
        return {"error": "Внутренняя ошибка бота"}


async def verificate_tilda_code(TILDA_SHEET_URL, code, uid="", uname=""):
    try:
        data = {
            "id": code,
            "uid": uid,
            "uname": uname
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(TILDA_SHEET_URL, json=data) as resp:  # [1]
                if resp.status == 404:
                    return {"error": f"Code verification link expired tell about it to admin"}
                return await resp.json()
    except Exception as err:
        return {"error": f"Code verification request fail :: <pre>{err}</pre>"}


if __name__ == "__main__":
    print(send_linkdata_to_sheet(1111, "dfsdfsdf", "dfsdfsdfsdfdsfsssdzxc", 11, "hfuyfuyuyf"))
