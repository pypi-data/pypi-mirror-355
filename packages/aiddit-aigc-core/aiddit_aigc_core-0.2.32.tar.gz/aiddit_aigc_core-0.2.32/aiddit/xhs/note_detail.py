import logging
import os
import requests
import json
import traceback
from tqdm import tqdm
import time
import aiddit.utils as utils
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
import uuid
from aiddit.model.gemini_upload_file import handle_file_path
from aiddit.tools.oss_upload import upload_oss
from tenacity import RetryError, retry_if_exception_type
from aiddit.exception.BizException import RetryIgnoreException


def get_note_detail(content_link):
    print(f"get note detail {content_link}")

    url = "http://crawler.aiddit.com/crawler/xiao_hong_shu/detail"

    payload = json.dumps({
        "content_link": content_link,
        "is_upload": True,
        "token": "3485b0234a05bf398c1da20069729036"
    })
    headers = {
        'Authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIn0.uU_4v9ukxon47prl6EEV2U5YqSIoJr8r6wS1SBnOJiA',
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    if response.status_code == 200:
        note_detail_response = json.loads(response.text)
        if note_detail_response.get("code") != 0:
            if note_detail_response.get("code") < 0:
                raise RetryIgnoreException(
                    f"Failed to get note detail {content_link} , code = {note_detail_response.get('code')} , {response.text}")
            else:
                raise Exception(
                    f"Exception: Failed to get note detail {content_link} , code = {note_detail_response.get('code')} , {response.text}")

        return note_detail_response.get("data").get("data")
    else:
        raise Exception(f"Failed to get note detail {content_link} , http status code = {response.status_code}")


from tenacity import retry, stop_after_attempt, wait_fixed


@retry(stop=stop_after_attempt(10), wait=wait_fixed(10))
def batch_get_note_detail_with_retries(note_dir):
    cached_cnt, total_cnt, success_cnt = batch_get_note_detail(note_dir)

    if cached_cnt + success_cnt < total_cnt:
        raise Exception(
            f"批量获取小红书详情失败, cached_cnt={cached_cnt}, total_cnt={total_cnt}, success_cnt={success_cnt}")
    pass


def batch_get_note_detail(note_dir):
    note_list = os.listdir(note_dir)

    success_cnt = 0
    cached_cnt = 0
    for note_filename in tqdm(note_list, desc=f"batch_get_note_detail , {os.path.basename(note_dir)}"):
        with open(os.path.join(note_dir, note_filename), 'r') as f:
            note = json.load(f)
            if not note.get("images"):
                while True:
                    try:
                        note_detail = get_note_detail(note.get("link"))
                        print(f"get note detail success {note.get('link')}")

                        note["comment_count"] = note_detail.get("comment_count")

                        note["images"] = [i.get("cdn_url", i.get("image_url")) for i in
                                          note_detail.get("image_url_list", [])]
                        note["like_count"] = note_detail.get("like_count")
                        note["body_text"] = note_detail.get("body_text")
                        note["title"] = note_detail.get("title")
                        note["collect_count"] = note_detail.get("collect_count")
                        note["link"] = note_detail.get("content_link")

                        content_type = note_detail.get("content_type")
                        note["content_type"] = content_type

                        if content_type == "video":
                            print(f"content_type is video , {json.dumps(note_detail, ensure_ascii=False, indent=4)}")

                        if content_type == "video" and note_detail.get("video_url_list") is not None and len(
                                note_detail.get("video_url_list", [])) > 0:
                            video = note_detail.get("video_url_list")[0]
                            xhs_cnd_video_url = video.get("video_url")
                            try:
                                video = note_detail.get("video_url_list", [])[0]
                                video_url = upload_video_2_oss(xhs_cnd_video_url)
                                video_info = {
                                    "origin_video_url": video.get("video_url"),
                                    "duration": video.get("video_duration"),
                                    "video_url": video_url
                                }
                                note["video"] = video_info
                            except Exception as e:
                                if isinstance(e, RetryError):
                                    e = e.last_attempt.exception()

                                note["video"] = {}
                                print(f"upload xhs video {xhs_cnd_video_url} error , {str(e)}")
                        else:
                            note["video"] = {}

                        with open(os.path.join(note_dir, note_filename), 'w') as wf:
                            json.dump(note, wf, ensure_ascii=False, indent=4)
                            success_cnt += 1
                        break
                    except Exception as e:
                        error = traceback.format_exc()
                        print(error)
                        print(f"Failed to get note detail , {e}")
                        if "访问频次异常" in error:
                            print(f"访问频次异常 sleep 3s")
                            time.sleep(3)
                        else:
                            break
            else:
                cached_cnt += 1
                print(f"note {note.get('link')} already has detail data")

    print(f"cached count = {cached_cnt} , total count = {len(note_list)} success count = {success_cnt}")
    return cached_cnt, len(note_list), success_cnt


def single_detail(link, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    note_id = link.split("?")[0].split("/")[-1]
    if os.path.exists(os.path.join(output_dir, f"{note_id}.json")):
        print(f"{note_id}.json already exists , skip , {link}")
        return

    note_detail = get_note_detail(link)
    print(note_detail)
    note = {}

    note["comment_count"] = note_detail.get("comment_count")
    note["images"] = [i.get("cdn_url", i.get("image_url")) for i in
                      note_detail.get("image_url_list", [])]
    note["like_count"] = note_detail.get("like_count")
    note["body_text"] = note_detail.get("body_text")
    note["title"] = note_detail.get("title")
    note["collect_count"] = note_detail.get("collect_count")
    note["link"] = note_detail.get("content_link")
    note["channel_content_id"] = note_detail.get("channel_content_id")

    content_type = note_detail.get("content_type")
    note["content_type"] = content_type
    if content_type == "video" and note_detail.get("video_url_list") is not None and len(
            note_detail.get("video_url_list", [])) > 0:
        video = note_detail.get("video_url_list")[0]
        xhs_cnd_video_url = video.get("video_url")
        try:
            video = note_detail.get("video_url_list", [])[0]
            video_url = upload_video_2_oss(xhs_cnd_video_url)
            video_info = {
                "origin_video_url": video.get("video_url"),
                "duration": video.get("video_duration"),
                "video_url": video_url
            }
            note["video"] = video_info
        except Exception as e:
            note["video"] = {}
            print(f"upload xhs video {xhs_cnd_video_url} error , {str(e)}")
    else:
        note["video"] = {}

    with open(os.path.join(output_dir, f"{note_detail.get('channel_content_id')}.json"), 'w') as wf:
        json.dump(note, wf, ensure_ascii=False, indent=4)


def upload_video_2_oss(video_url):
    video_name = f"{uuid.uuid4().int}.mp4"
    local_path = handle_file_path(video_url, video_name)
    key = f"aigc_creation/xhs/video/{video_name}"
    oss_url = upload_oss(key, local_path)
    print(f"upload_video_2_oss {video_url} to {oss_url}")
    return oss_url


def refresh_detail_images():
    refresh_dir = "/image_article_comprehension/aiddit/create/reference_note_keypoint/image_merge_0102_1230"
    total_count = len(os.listdir(refresh_dir))

    files = os.listdir(refresh_dir)
    files = ["67752b32000000000900c5cc.json"]

    success_cnt = 0
    for i in tqdm(files):
        try:
            note = json.load(open(os.path.join(refresh_dir, i), 'r'))

            if any("res.cybertogether.net" in images_url for images_url in note.get("note_info").get("images")):
                print(f"{json.dumps(note.get('note_info').get('images'))} has res.cybertogether.net , skip")
                continue

            note_detail = get_note_detail(note.get("note_info").get("link"))

            note["note_info"]["images"] = [i.get("cdn_url", i.get("image_url")) for i in
                                           note_detail.get("image_url_list", [])]

            utils.save(note, os.path.join(refresh_dir, i))
            success_cnt += 1
        except Exception as e:
            print("Failed to refresh detail images", i, str(e))

    print(f"success count = {success_cnt} / {total_count}")
    pass


def refresh_crawler_detail_images():
    refresh_dir = "/image_article_comprehension/aiddit/comprehension/note_data/account_猫小司_6430bea30000000012011f2d"
    total_count = len(os.listdir(refresh_dir))

    files = os.listdir(refresh_dir)

    success_cnt = 0
    for i in tqdm(files):
        try:
            note = json.load(open(os.path.join(refresh_dir, i), 'r'))

            if any("res.cybertogether.net" in images_url for images_url in note.get("images")):
                print(f"{json.dumps(note.get('images'))} has res.cybertogether.net , skip")
                continue

            note_detail = get_note_detail(note.get("link").split("?")[0])

            print(f"{json.dumps(note_detail, ensure_ascii=False, indent=4)}")

            note["images"] = [i.get("cdn_url", i.get("image_url")) for i in
                              note_detail.get("image_url_list", [])]

            utils.save(note, os.path.join(refresh_dir, i))
            success_cnt += 1
        except Exception as e:
            print("Failed to refresh detail images", i, str(e))

    print(f"success count = {success_cnt} / {total_count}")
    pass


def simplify_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    # 保留需要的参数
    simplified_query_params = {
        'xsec_token': query_params.get('xsec_token', [''])[0]
    }

    # 构建新的URL
    simplified_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.params,
        urlencode(simplified_query_params),
        parsed_url.fragment
    ))

    return simplified_url


if __name__ == "__main__":
    ans = get_note_detail(
        "https://www.xiaohongshu.com/explore/67e985e0000000001c0017e6?xsec_source=app_share&xsec_token=CB29WSSFRyuggA-mt4JN-ZjsQp3UVppAXpEREf0EJghK0=")
    print(ans)
    pass
