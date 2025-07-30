import requests
import os
import json
import time


def try_run(id: str, arguments: dict, biz_id: str = "") -> str:
    url = "http://aigc-api.cybertogether.net/aigc/agent/tools/tryRun"

    payload = json.dumps({
        "params": {
            "id": id,
            "argumentsMap": arguments,
            "bizId": biz_id
        },
        "baseInfo": {
            "token": "adc66c43c41b4fd3b7936f5b9894efb5",
            "appType": 9,
            "platform": "pc",
            "appVersionCode": 1000,
            "clientTimestamp": 1,
            "fid": 1,
            "loginUid": 1,
            "pageSource": 1,
            "requestId": 1,
            "rid": 1,
            "uid": 1
        }
    })
    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json',
        'Origin': 'http://aigc-admin.cybertogether.net',
        'Pragma': 'no-cache',
        'Proxy-Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    data = json.loads(response.text)

    if data.get("code") == 0:

        data = data.get("data", {})
        status = data.get('status')

        if status == 1:
            try:
                return json.dumps(json.loads(data.get("result")), ensure_ascii=False, indent=4)
            except Exception as e:
                return data.get("result")
        elif status == 0:
            # 未完成
            biz_id = data.get('bizId')
            time.sleep(10)
            return try_run(id=id, arguments=arguments, biz_id=biz_id)
        else:
            raise Exception(f"Unknown status code returned from API : status = {status}")

    else:
        return f"Error: {data.get('message')}"


if __name__ == "__main__":
    result = try_run("xhs_search_by_keyword", {
        "keyword": "哈哈哈"
    })

    print(result)
