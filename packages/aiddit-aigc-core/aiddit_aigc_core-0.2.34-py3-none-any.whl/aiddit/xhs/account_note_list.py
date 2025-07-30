import logging

import requests
import json
import os
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_not_exception_type, RetryError
from aiddit.exception.BizException import RetryIgnoreException


@retry(stop=stop_after_attempt(2), wait=wait_fixed(2), retry=retry_if_not_exception_type(RetryIgnoreException))
def save_account_note(account_id, account_name, save_dir):
    # dir_name = f"account_{account_name}_{account_id}"
    # dir = f"{save_dir}/{dir_name}"
    os.makedirs(save_dir, exist_ok=True)

    url = "http://crawler.aiddit.com/crawler/xiao_hong_shu/blogger"
    payload = json.dumps({
        "account_id": account_id,
        "cursor": "",
        "token": "3485b0234a05bf398c1da20069729036"
    })
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()

    response_data = json.loads(response.text)
    if response_data.get("code", -1) < 0:
        raise RetryIgnoreException(f"获取用户历史帖子  {account_id} response code != 0, {response.text}")
    elif response_data.get("code", -1) > 0:
        raise Exception(f"获取用户历史帖子  {account_id} response code != 0, {response.text}")

    # print(response.text)
    data = response_data.get("data", {}).get("data")

    if data is None or len(data) == 0:
        raise Exception(f"no data for account_id {account_id} , {response.text}")

    # data = user_note_list(account_id)

    logging.info(f"{account_id} {account_name} note count: {len(data)}")

    for d in data:
        # print(json.dumps(d))
        note_id = d["note_id"]
        xsec_token = d.get("xsec_token", "")
        note_url = f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}"

        file_name = f"{note_id}.json"

        note_info = {
            "channel_content_id": note_id,
            "link": note_url,
            "xsec_token": xsec_token
        }

        if os.path.exists(f"{save_dir}/{file_name}") is True:
            print(f"file exists {file_name}")
            continue

        with open(os.path.join(save_dir, file_name), 'a') as f:
            f.write(json.dumps(note_info, ensure_ascii=False, indent=4))

    return save_dir


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_not_exception_type(RetryIgnoreException))
def get_account_info(account_id):
    url = "http://crawler.aiddit.com/crawler/xiao_hong_shu/account_info"

    payload = json.dumps({
        "account_id": account_id,
        "token": "3485b0234a05bf398c1da20069729036"
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)

    response.raise_for_status()

    response_data = json.loads(response.text)
    if response_data.get("code", -1) < 0:
        raise RetryIgnoreException(f"get_account_info  {account_id} response code != 0, {response.text}")
    elif response_data.get("code", -1) > 0:
        raise Exception(f"get_account_info  {account_id} response code != 0, {response.text}")

    data = response_data.get("data", {}).get("data")

    if data is None:
        raise Exception(f"no data for account_id {account_id} , {response.text}")

    if data.get("account_name") is None:
        raise Exception(f"account_name is None, please check the account_id {account_id}")

    return {
        "account_name": data.get("account_name"),
        "description": data.get("description"),
        "avatar_url": data.get("avatar_url"),
        "account_id": account_id,
        "account_link": data.get("account_link"),
    }


if __name__ == '__main__':
    # 修改变量account_id start
    # account_阿橘的小窝_5bb61a0a59b9bf0001e9a986.txt
    # account_id = "5bb61a0a59b9bf0001e9a986"
    # account_name = "阿橘的小窝"
    # dir = f"/Users/nieqi/Documents/workspace/python/image_article_comprehension/aiddit/comprehension/note_data"
    # dir_name = f"account_{account_name}_{account_id}"
    # save_dir = f"{dir}/{dir_name}"
    # # save_account_note(account_id, account_name, save_dir)
    #
    # note_detail.batch_get_note_detail(save_dir)

    # print(json.dumps(get_account_info(account_id), ensure_ascii=False, indent=4))

    ans = save_account_note("617a100c000000001f03f0b9", "小红书用户",
                            "/Users/nieqi/Documents/workspace/python/image_article_comprehension/aiddit/comprehension/note_data/account_note")
    print(ans)
