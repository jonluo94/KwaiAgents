#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: luo
import json
import os

from translate import Translator

from diffusion.client import call_diffusion_gen
from kwaiagents.tools.base import BaseResult, BaseTool

DIFFUSION_SERVER_URL = os.getenv("DIFFUSION_SERVER_URL") if os.getenv(
    "DIFFUSION_SERVER_URL") else "http://127.0.0.1:8080"

def translate_en_text(text):
    translator = Translator(from_lang="zh",to_lang="en")
    translation = translator.translate(text)
    return translation

class DiffusionResult(BaseResult):
    @property
    def answer(self):
        if not self.json_data:
            return ""
        else:
            item = self.json_data
            res = json.dumps(item)
            if "error" in res:
                return f'请求图片生成服务报错'
            rst = item["image"]
            return rst


class DiffusionTool(BaseTool):
    """
    generate image by entering the  prompt in English, and return the URL of the image.

    Args:
        prompt (str): Keywords must be in English or translated into English that describe what you want the image to have.

    Returns:
        str: the URL of the generated image.
    """
    name = "image_gen"
    zh_name = "文生图"
    description = 'Image Gen:"image_gen", args:"prompt": "<str: prompt keywords in English, required>"'
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

    def __call__(self, prompt, *args, **kwargs):
        try:
            image_url_json = call_diffusion_gen(server=DIFFUSION_SERVER_URL, prompt=translate_en_text(prompt))
        except Exception:
            image_url_json = {"error": "http request error"}

        return DiffusionResult(image_url_json)
