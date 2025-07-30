import requests
import json
import aiddit.api.unit_test.try_run_tools as try_run_tools


def get_weather(city: str) -> str:
    """get the current weather for a specific city.

    Args:
        city: The name of the city to get the weather for.

    Returns:
        A string describing the current weather in the specified city.
    """
    return f"The weather in {city} is sunny with a high of 25°C and a low of 15°C."


def get_longitude_and_latitude(city: str) -> str:
    """get the longitude and latitude for a specific city.

    Args:
        city: The name of the city to get the longitude and latitude for.

    Returns:
        A string describing the longitude and latitude of the specified city.
    """
    return f"The longitude and latitude of {city} are 120.0° E and 30.0° N."


def comprehension_xhs_history_note_by_user_id(xhs_user_id: str, comprehension_requirements: str) -> str:
    """comprehend the history notes of a user on xiaohongshu for a specific requirements.

    Args:
        xhs_user_id: The user ID of the xiaohongshu account.
        comprehension_requirements: The requirements for comprehension.

    Returns:
        A string summarizing the user's history notes based on the comprehension requirements.
    """

    url = "http://localhost:8010/aigc/creation/create/persona/comprehension_xhs_history_note_by_user_id"

    payload = json.dumps({
        "xhs_user_id": xhs_user_id,
        "comprehension_requirements": comprehension_requirements
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()

    data = json.loads(response.text)

    if data.get("code") == 0:
        return json.dumps(data.get("data"), ensure_ascii=False, indent=4)
    else:
        return f"Error: {data.get('message')}"


def persona_by_user_id(xhs_user_id: str) -> str:
    """根据小红书用户 user_id 获取其人设的选题创作信息

    Args:
        xhs_user_id: The user ID of the xiaohongshu account.

    Returns:
        A string summarizing the user's persona.
    """

    url = "http://localhost:8010/aigc/creation/create/topic/persona_by_user_id"

    payload = json.dumps({
        "xhs_user_id": xhs_user_id
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()

    data = json.loads(response.text)
    if data.get("code") == 0:
        return json.dumps(data.get("data"), ensure_ascii=False, indent=4)
    else:
        return f"Error: {data.get('message')}"


def xhs_search_by_keyword(keyword: str):
    """小红书搜索，结果按照点赞数排序（从高到低）

    args:
        keyword: The keyword to search for on xiaohongshu.

    Returns:
        A list of dictionaries containing the search results
    """

    return try_run_tools.try_run("xhs_search_by_keyword", arguments={
        "keyword": keyword
    })