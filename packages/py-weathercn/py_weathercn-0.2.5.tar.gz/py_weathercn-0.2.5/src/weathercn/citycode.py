import requests
import json
from time import time


def get_code_from_name(name: str) -> str:
    url = "http://toy1.weather.com.cn/search?cityname={city}&callback=&_={time}".format(city=name, time=int(time() * 1000))
    headers = {
        "Sec-Fetch-Dest": "script",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "same-site",
        "Sec-GPC": "1",
        "Referer": "https://www.weather.com.cn/",
    }

    req = requests.get(url, cookies={"f_city": "beijing"}, headers=headers)
    results = json.loads(req.text[1:-1])
    for r in results:
        return r['ref'].split("~")[0]

def get_code(name: str) -> str:
    if name.isnumeric():
        return name
    return get_code_from_name(name)
