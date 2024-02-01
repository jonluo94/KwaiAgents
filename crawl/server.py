import argparse
import asyncio
import time
from typing import Union

import pydantic
from pydantic import BaseModel
import uvicorn
from fastapi import Query, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from crawl.bilibili.crawler import BilibiliCrawler

bilibili_crawler = BilibiliCrawler()


class Response(BaseModel):
    data: Union[str, dict] = pydantic.Field("", description="data")


async def run_bilibili_crawl(query: Union[str, None] = Query(alias="query")):
    task_id = time.thread_time_ns()
    bilibili_crawler.crawl_video_reply(task_id, query)
    return Response(data=task_id)


async def get_bilibili_crawl_result(task_id: Union[int, None] = Query(alias="task_id")):
    data = bilibili_crawler.get_crawl_task_result(task_id)
    return Response(data=data)


def api_start(host, port):
    global app
    global sd
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.get("/bilibili_crawl/run", response_model=Response)(run_bilibili_crawl)
    app.get("/bilibili_crawl/result", response_model=Response)(get_bilibili_crawl_result)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--host", type=str, default="127.0.0.1", help="host ip")
    parser.add_argument("--port", type=int, default=7070, help="port")
    args = parser.parse_args()

    api_start(args.host, args.port)
