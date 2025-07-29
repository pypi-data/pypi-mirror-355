#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Project      : AI.  @by PyCharm
# @File         : videos
# @Time         : 2025/6/11 15:13
# @Author       : betterme
# @WeChat       : meutils
# @Software     : PyCharm
# @Description  : 

from meutils.pipe import *
from meutils.decorators.retry import retrying
from meutils.llm.clients import AsyncClient
from meutils.schemas.openai_types import CompletionRequest
from meutils.notice.feishu import send_message_for_volc as send_message

from meutils.db.redis_db import redis_aclient
from meutils.llm.check_utils import check_token_for_volc
from meutils.config_utils.lark_utils import get_next_token_for_polling, get_series

from fastapi import APIRouter, File, UploadFile, Query, Form, Depends, Request, HTTPException, status, BackgroundTasks

# Please activate
FEISHU_URL = "https://xchatllm.feishu.cn/sheets/GYCHsvI4qhnDPNtI4VPcdw2knEd?sheet=8W6kk8"  # 超刷


async def get_valid_token():
    tokens = await get_series(FEISHU_URL)
    for token in tokens:
        if await check_token_for_volc(token):
            logger.debug(f"有效 {token}")

            return token
        else:
            logger.debug(f"无效 {token}")
    _ = f"{FEISHU_URL}\n\n所有token无效"
    logger.error(_)
    send_message(_, n=3)


@retrying(max_retries=5)
async def create_task(request: CompletionRequest, api_key: Optional[str] = None):
    api_key = api_key or await get_next_token_for_polling(feishu_url=FEISHU_URL, from_redis=True, check_token=check)

    payload = {
        "model": "doubao-seedance-1-0-pro-250528",
        "content": [
            {
                "type": "text",
                "text": "无人机以极快速度穿越复杂障碍或自然奇观，带来沉浸式飞行体验  --resolution 1080p  --duration 5 --camerafixed false"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/seepro_i2v.png"
                }
            }
        ]
    }
    payload = request.model_dump(exclude_none=True)
    client = AsyncClient(base_url="https://ark.cn-beijing.volces.com/api/v3", api_key=api_key)

    response = await client.post(
        path="/contents/generations/tasks",
        cast_to=object,
        body=payload
    )

    if task_id := response.get('id'):
        await redis_aclient.set(task_id, api_key, ex=7 * 24 * 3600)

    return response  # {'id': 'cgt-20250611152553-r46ql'}


async def get_task(task_id: str):
    token = await redis_aclient.get(task_id)  # 绑定对应的 token
    token = token and token.decode()
    if not token:
        raise HTTPException(status_code=404, detail="TaskID not found")

    client = AsyncClient(base_url="https://ark.cn-beijing.volces.com/api/v3", api_key=api_key)

    response = await client.get(
        path=f"/contents/generations/tasks/{task_id}",
        cast_to=object,
    )

    return response


# 执行异步函数
if __name__ == "__main__":
    # api_key = "07139a08-e360-44e2-ba31-07f379bf99ed"  # {'id': 'cgt-20250611164343-w2bzq'} todo 过期调用get

    api_key = "b4c77fc4-b0a1-43e9-b151-9cea13fcc04d"  # 欠费

    request = CompletionRequest(
        model="doubao-seedance-1-0-pro-250528",
        content=[
            {
                "type": "text",
                "text": "无人机以极快速度穿越复杂障碍或自然奇观，带来沉浸式飞行体验  --resolution 1080p  --duration 5 --camerafixed false"
            },

            {
                "type": "image_url",
                "image_url": {
                    "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/seepro_i2v.png"
                }
            }
        ]
    )
    # r = arun(create_task(request, api_key))
    # r = {'id': 'cgt-20250612172542-6nbt2'}

    # arun(get_task(r.get('id')))

    # arun(get_task("cgt-20250611164343-w2bzq"))

    # arun(get_task("cgt-20250611193213-tcqth"))

    arun(get_valid_token())

"""
openai.NotFoundError: Error code: 404 - {'error': {'code': 'ModelNotOpen', 'message': 'Your account 2107813928 has not activated the model doubao-seedance-1-0-pro. Please activate the model service in the Ark Console. Request id: 021749718307793fc1441381f8ed755824bb9d58a45ee6cb04068', 'param': '', 'type': 'NotFound'}}


curl -X POST https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 29ce2c44-981d-4b7b-b0f5-f8a39586fd06" \
  -d '{
    "model": "doubao-seaweed-241128",
    "content": [
        {
            "type": "text",
            "text": "女孩抱着狐狸，女孩睁开眼，温柔地看向镜头，狐狸友善地抱着，镜头缓缓拉出，女孩的头发被风吹动  --resolution 720p --duration 5"
        },
        {
            "type": "image_url",
            "image_url": {
                "url": "https://ark-project.tos-cn-beijing.volces.com/doc_image/i2v_foxrgirl.png"
            }
        }
    ]
}'
"""
