#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : MeUtils.
# @File         : json_utils
# @Time         : 2021/4/22 1:51 下午
# @Author       : yuanjie
# @WeChat       : 313303303
# @Software     : PyCharm
# @Description  : pd.io.json.json_normalize

# https://mangiucugna.github.io/json_repair/
# https://jsonpath.com/

import jsonpath

# json https://blog.csdn.net/freeking101/article/details/103048514
# https://github.com/ijl/orjson#quickstart
# https://jmespath.org/tutorial.html
# https://goessner.net/articles/JsonPath/
# https://www.jianshu.com/p/3f5b9cc88bde

# todo: jsonpath jmespath
# https://blog.csdn.net/be5yond/article/details/118976017
# https://blog.csdn.net/weixin_44799217/article/details/127590589

from meutils.pipe import *
from json_repair import repair_json


def json2class(dic, class_name='Test'):
    s = f"""class {class_name}(BaseModel):"""
    for k, v in dic.items():
        _type = type(v).__name__
        if isinstance(_type, str):
            v = f"'{v}'"
        s += f"\n\t{k}: {_type} = {v}"

    print(s)


@lru_cache(1024)
def json_loads(s):
    if isinstance(s, bytes):
        s = s.decode()
    try:
        return json.loads(s.replace("'", '"'))

    except Exception as e:
        logger.warning(e)

        return eval(s)


def json_path(obj, expr):  # todo: 缓存
    """$..["keywords","query","search_result"]"""
    if isinstance(obj, dict):
        pass
    elif isinstance(obj, str):
        obj = json_repair.loads(obj)
    elif isinstance(obj, bytes):
        obj = json_repair.loads(obj.decode())
    elif isinstance(obj, BaseModel):
        obj = obj.dict()

    return jsonpath.jsonpath(obj, expr=expr)


if __name__ == '__main__':
    print(json_path({"a": 1}, expr='$.a'))
    print(json_path("""{"a": 1}""", expr='$.a'))

    json_string = """{"a": 1}"""


    class A(BaseModel):
        a: int = 1


    print(json_path(A(), '$.a'))

    json2class(
        {
            "id": 3323,
            "type": 1,
            "key": "20c790a8-8f5b-4382-942f-05d6f93ce04d:c3ceee990d5aae3f99084e7da6fa7c98",
            "access_token": "",
            "openai_organization": "",
            "test_model": "",
            "status": 1,
            "name": "fal-flux",
            "weight": 0,
            "created_time": 1749175121,
            "test_time": 0,
            "response_time": 0,
            "base_url": "https://openai.chatfire.cn/images",
            "other": "",
            "balance": 0,
            "balance_updated_time": 0,
            "models": "imagen4,recraft-v3,recraftv3,flux-pro-1.1-ultra,flux-kontext-pro,flux-kontext-max",
            "group": "default",
            "used_quota": 9927600,
            "upstream_user_quota": 0,
            "model_mapping": "{\n \"flux-pro-1.1-ultra\": \"fal-ai/flux-pro/v1.1-ultra\",\n \"ideogram-ai/ideogram-v2-turbo\": \"fal-ai/ideogram/v2/turbo\",\n \"ideogram-ai/ideogram-v2\": \"fal-ai/ideogram/v2\",\n \"recraftv3\": \"fal-ai/recraft-v3\",\n \"recraft-v3\": \"fal-ai/recraft-v3\",\n \"imagen4\": \"fal-ai/imagen4/preview\",\n \"flux-kontext-pro\": \"fal-ai/flux-pro/kontext\",\n \"flux-kontext-max\": \"fal-ai/flux-pro/kontext/max\",\n \"imagen4,recraft-v3,recraftv3,flux-pro-1.1-ultra,flux-kontext-pro,flux-kontext-max\": \"\"\n}",
            "headers": "",
            "status_code_mapping": "",
            "priority": 1,
            "auto_ban": 1,
            "empty_response_retry": 0,
            "not_use_key": 0,
            "remark": "",
            "mj_relax_limit": 99,
            "mj_fast_limit": 99,
            "mj_turbo_limit": 99,
            "other_info": "{\"status_reason\":\"model: flux-kontext-max, status code: 500, reason: Failed to generate image: User is locked. Reason: Exhausted balance. Top up your balance at fal.ai/dashboard/billing.\",\"status_time\":1749175757}",
            "channel_ratio": 1,
            "error_return_429": 0,
            "tag": "fal",
            "setting": "",
            "param_override": "",
            "is_tools": True
        }
    )