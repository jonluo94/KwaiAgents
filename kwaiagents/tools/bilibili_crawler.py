#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: luo
import json
import os

from crawl.client import call_bilibili_crawl
from kwaiagents.tools.base import BaseResult, BaseTool

BILIBILI_CRAWLER_SERVER_URL = os.getenv("BILIBILI_CRAWLER_SERVER_URL") if os.getenv(
    "BILIBILI_CRAWLER_SERVER_URL") else "http://127.0.0.1:7070"

class BilibiliCrawlerResult(BaseResult):
    @property
    def answer(self):
        if not self.json_data:
            return ""
        else:
            item = self.json_data
            res = json.dumps(item)
            if "error" in res:
                return f'请求哔哩哔哩爬虫服务报错'
            rst = item["data"]
            return f"爬虫已执行,执行任务id: {rst}"


class BilibiliCrawlerTool(BaseTool):
    """
    Complete crawler related tasks

    Args:
        query (str): The relevant information of crawler.

    Returns:
        str: the task id of crawler.
    """
    name = "bilibili_crawler"
    zh_name = "哔哩哔哩爬虫"
    description = 'Bilibili Crawler:"bilibili_crawler", args:"query": "<str: The relevant information of crawler, required>"'
    tips = ""

    def __init__(
            self,
            lang="wt-wt",
            max_retry_times=5,
            *args,
            **kwargs,
    ):
        self.max_retry_times = max_retry_times
        self.lang = lang

    def __call__(self, query, *args, **kwargs):
        try:
            image_url_json = call_bilibili_crawl(server=BILIBILI_CRAWLER_SERVER_URL, query=query)
        except Exception:
            image_url_json = {"error": "http request error"}

        return BilibiliCrawlerResult(image_url_json)
