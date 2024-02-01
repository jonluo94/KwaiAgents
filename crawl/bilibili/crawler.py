# -*- coding: utf-8 -*-
import time
from traceback import print_exc
import asyncio
import httpx
import json
from typing import List, Dict, Any, TypeAlias, Optional

from bilibili_api import Credential, search, sync
import os

from crawl.async_pool import AsyncPool
from crawl.bilibili.login import login_bilibili

JSON_TYPE: TypeAlias = Dict[str, Any]
# 同时最多运行多少个协程，可调，但不建议改太大，不要给 B 站造成负担
ASYNC_POOL_MAX_SIZE = 16
# 对话链的最短有效长度，超过此长度的对话才会被保存
MIN_DIALOG_LENGTH = 0
# 爬取每一页评论（即视频下面）后的休眠时间，单位秒
SLEEP_TIME_ONE_PAGE = 0.1
# 爬取每一条评论后的休眠时间，单位秒
SLEEP_TIME_ONE_REPLY = 0.1
# 被 B 站限制访问时的休眠时间，单位秒
SLEEP_TIME_WHEN_LIMITED = 30
# 被 B 站限制访问时的最高重试次数，超过此次数则放弃
MAX_RETRY_TIME_WHEN_LIMITED = 3
# 当某条数据已经爬过时，是否跳过，而不是重新爬取（对于新视频，有可能评论会随时间更新；老视频一般无影响）
SKIP_EXISTED_DATA = True

# 爬取时的公共请求头
COMMON_HEADERS = {
    "Origin": "https://www.bilibili.com",
    "Authority": "api.bilibili.com",
    "Sec-Ch-Ua": '"Chromium";v="116", "Not)A;Brand";v="24", "Microsoft Edge";v="116"',
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
}

BILIBILI_CRAWLER_DATA_PATH = os.getenv("BILIBILI_CRAWLER_DATA_PATH") if os.getenv(
    "BILIBILI_CRAWLER_DATA_PATH") else "data"


class BilibiliCrawler:
    pool = AsyncPool(maxsize=ASYNC_POOL_MAX_SIZE)

    def __init__(self):
        credential_cookies = login_bilibili()
        self.credential = Credential(sessdata=credential_cookies["SESSDATA"],
                                     bili_jct=credential_cookies["bili_jct"],
                                     buvid3=credential_cookies["buvid3"],
                                     dedeuserid=credential_cookies["DedeUserID"],
                                     ac_time_value=credential_cookies["ac_time_value"])

    async def _refresh_cookie_if_necessary(self):
        need_refresh = await self.credential.check_refresh()
        if need_refresh:
            print("cookie 已过期，正在刷新")
            await self.credential.refresh()
            print("cookie 刷新成功")
        else:
            print("cookie 未过期，无需刷新")

    async def get_one_page(self, oid: int, pagination_str: str, client: httpx.AsyncClient = None):
        """获取范围：一个回复页"""
        params = {
            "type": 1,
            "oid": oid,
            "mode": 3,
            "pagination_str": '{"offset":"%s"}' % pagination_str.replace('"', r"\""),
        }

        url = "https://api.bilibili.com/x/v2/reply/main"

        text = await get_html(url, params, COMMON_HEADERS, cookies=self.credential.get_cookies(), client=client)
        if text is None:
            return []
        obj = json.loads(text)
        return obj

    async def crawl_one_video(self, task_id, oid: int, video_title: str):
        """
        爬取一个视频的所有评论
        """
        print("- 开始爬取视频 {} 的评论".format(oid))
        url = "https://api.bilibili.com/x/v2/reply/count"
        params = {
            "type": 1,
            "oid": oid
        }
        text = await get_html(url, params, COMMON_HEADERS)
        obj = json.loads(text)
        total_page: int = obj["data"]["count"] // 20 + 1
        print("- 视频 {} 一共有 {} 页评论".format(oid, total_page))
        pagination = ''
        async with httpx.AsyncClient() as client:
            for page in range(1, total_page + 1):
                next_page = await self.crawl_one_page_video(task_id, oid, video_title, page, pagination_str=pagination,
                                                            client=client)

                print("-- 爬取视频 {} 的第 {} 页评论完毕，下一页: {}".format(oid, page, next_page))
                if next_page is None:
                    print("- 视频 {} 的评论爬取完毕".format(oid))
                    break
                await asyncio.sleep(SLEEP_TIME_ONE_PAGE)
                pagination = next_page

    async def crawl_one_page_video(self, task_id, oid: int, video_title: str, page: int, pagination_str: str,
                                   client: httpx.AsyncClient) -> \
            Optional[str]:
        """
        爬取一个视频一页的评论，返回下一页的 pagination_str
        """

        print("-- 开始爬取视频 {} 的第 {} 页评论".format(oid, page))
        obj = await self.get_one_page(oid, pagination_str, client)

        if obj["code"] != 0:
            print("爬取视频 {} 的第 {} 页评论失败，原因是 {} (code={})".format(
                oid, page, obj["message"], obj["code"]))
            return None
        video_replies = obj["data"]["replies"]
        for root_reply in video_replies:
            saved_file_name = os.path.join(BILIBILI_CRAWLER_DATA_PATH,
                                           f"task_{task_id}/video_{oid}/page_{page}/rpid_{root_reply['rpid']}_convs.json")
            if SKIP_EXISTED_DATA and os.path.exists(saved_file_name):
                print("--- rpid 为 {:12d} 的评论已经爬过，跳过爬取".format(root_reply["rpid"]))
                continue
            comment_replies: Dict[str, Any] = await self.get_reply(oid, root_reply["rpid"], root_reply["rcount"])
            conversations = build_conv_from_replies(root_reply, comment_replies,video_title)
            if conversations:
                save_obj(conversations, saved_file_name)
                print("--- 保存 rpid 为 {:12d} 的评论并构建对话完毕，共 {:6d} 条".format(
                    root_reply["rpid"], len(conversations)))
            else:
                print("--- rpid 为 {:12d} 的评论没有符合要求的对话，跳过保存".format(root_reply["rpid"]))
            await asyncio.sleep(SLEEP_TIME_ONE_REPLY)

        if len(video_replies) > 0:
            print("爬取到的第 {} 页，第一条评论是 {}".format(
                page, video_replies[0]["content"]["message"]))
        return obj["data"]["cursor"]["pagination_reply"].get("next_offset")

    async def get_reply(self, oid: int, r_root: int, total_count: int):
        """获取某个楼层的所有回复"""
        total_page = total_count // 20 + 1
        replies = []
        for page in range(1, total_page + 1):
            if page % 10 == 0:
                print("---- 正在爬取 r_root: {}, page: {}".format(r_root, page))
            self.pool.submit(get_one_page_reply(oid, page, r_root),
                             callback=lambda future: replies.extend(future.result()))
        self.pool.wait()
        return replies

    async def crawl_video(self, task_id, query, top_n):
        # running
        self.save_crawl_task_result(task_id, query, "running")

        try:
            await self._refresh_cookie_if_necessary()
            res = await search.search(query)

            for r in res["result"]:
                if r["result_type"] != "video":
                    continue
                i = 0
                for data in r["data"]:
                    i = i + 1
                    if i > top_n:
                        break
                    print("+ 任务 {}".format(i))
                    video_id = data["id"]
                    video_title = data["title"]
                    await self.crawl_one_video(task_id, video_id, video_title)
        except Exception as e:
            print_exc()
            self.save_crawl_task_result(task_id, status="failed", data=f"error:{e}")
            return
        # 整理爬虫结果
        # 遍历文件夹的所有目录下的json文件
        self.get_crawl_task_data(task_id)
        # finished
        self.save_crawl_task_result(task_id, status="finished")

    def crawl_video_reply(self, task_id, query, top_n=1):
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.crawl_video(task_id, query, top_n))
        except Exception:
            pass

    def get_crawl_task_data(self, task_id):
        # Walk through the directory
        saved_task_path = os.path.join(BILIBILI_CRAWLER_DATA_PATH, f"task_{task_id}")
        user_reply = "user,reply\n"
        for root, dirs, files in os.walk(saved_task_path):
            for file in files:
                if not file.endswith('.json') or file == "result.json":
                    continue
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    datas = json.load(f)
                for data in datas:
                    is_one = True
                    for d in data:
                        user = d["from"]
                        reply = d["value"].replace('\n', '')
                        if is_one:
                            user_reply += f"{user},{reply}\n"
                        else:
                            user_reply += f"- {user},{reply}\n"
                        is_one = False
        print(user_reply)

    def save_crawl_task_result(self, task_id, query=None, status=None, data=None):
        saved_result_json = os.path.join(BILIBILI_CRAWLER_DATA_PATH, f"task_{task_id}/result.json")
        if os.path.exists(saved_result_json):
            with open(saved_result_json) as f:
                result = json.load(f)
            result["query"] = query if query else result["query"]
            result["status"] = status if status else result["status"]
            result["data"] = data if data else result["data"]
            save_obj(result, saved_result_json)
        else:
            save_obj({"status": status, "query": query, "data": data}, saved_result_json)

    def get_crawl_task_result(self, task_id) -> dict:
        saved_result_json = os.path.join(BILIBILI_CRAWLER_DATA_PATH, f"task_{task_id}/result.json")
        with open(saved_result_json) as f:
            result = json.load(f)
            return result


def save_obj(obj: JSON_TYPE, filename: str):
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


async def get_html(url: str, params: Dict = None, headers: Dict = None, cookies: Dict = None, timeout: int = 60,
                   client: httpx.AsyncClient = None, retry_time: int = 0):
    m_client = client
    try:
        if client is None:
            m_client = httpx.AsyncClient()
        # print("当前发送请求的 client ID: ", id(m_client))
        r = await m_client.get(url, timeout=timeout, params=params, headers=headers, cookies=cookies)
        if r.status_code == 412:
            if retry_time >= MAX_RETRY_TIME_WHEN_LIMITED:
                print("请求频率过高，引发 B 站限流了，已达到最大重试次数，放弃重试，尝试结束应用")
                os._exit(1)
            print(
                f"请求频率过高，引发 B 站限流了，我正在尝试休眠 {SLEEP_TIME_WHEN_LIMITED}s... （当前重试次数: {retry_time}）")
            await asyncio.sleep(SLEEP_TIME_WHEN_LIMITED)
            return await get_html(url, params, headers, cookies, timeout, client, retry_time + 1)
        r.raise_for_status()  # 如果状态不是200，引发HTTPError异常
        return r.text
    except Exception as e:
        print(e)
    finally:
        if client is None and m_client is not None:
            await m_client.aclose()


# https://api.bilibili.com/x/v2/reply/reply?csrf=9b261f0d10434bbefd17d7f4bd8247f2&oid=2&pn=1&ps=10&root=917945205&type=1
async def get_one_page_reply(oid: int, page: int, r_root: int):
    """获取一楼的一页评论"""
    params = {
        "type": 1,
        "oid": oid,
        "ps": 20,
        "pn": page,
        "root": r_root
    }
    url = "https://api.bilibili.com/x/v2/reply/reply"
    text = await get_html(url, params, COMMON_HEADERS)
    if text is None:
        return []
    obj = json.loads(text)
    print("爬取 r_root: {}, page: {} 完毕".format(r_root, page))
    await asyncio.sleep(0.01)
    return obj["data"].get("replies") or []


def build_conv_from_replies(root_reply: JSON_TYPE, replies: List[JSON_TYPE],video_title:str) -> List[List[Dict]]:
    if not replies:
        return [[{
            'value': root_reply['content']['message'],
            'from': root_reply['member']['uname'],
            "video":video_title,
        }]]

    conv = []
    replies_dict = {}
    replies.insert(0, root_reply)

    # 将replies数据转换成字典形式
    for reply in replies:
        rpid = reply['rpid']
        parent = reply['parent']
        content = reply['content']['message']
        uname = reply['member']['uname']
        replies_dict[rpid] = {'parent': parent,
                              'content': content, 'uname': uname}

    conv_tree = {}

    # 构建对话树
    for reply_id, reply in replies_dict.items():
        parent_id = reply['parent']
        if parent_id in conv_tree:
            conv_tree[parent_id].append(reply_id)
        else:
            conv_tree[parent_id] = [reply_id]

    # print(conv_tree)
    longest_paths = []
    path = []

    # DFS遍历所有根节点到叶子节点的路径
    def dfs(node):
        nonlocal path
        path.append(node)
        if node not in conv_tree:
            # 当前节点是叶子节点，保存路径
            longest_paths.append(path.copy())
        else:
            for child in conv_tree[node]:
                dfs(child)
        path.pop()

    # 从每个根节点开始进行DFS搜索
    for root in conv_tree[0]:
        dfs(root)

    # 根据路径获取对话链
    longest_conversations = []
    for path in longest_paths:
        conversation = []
        for node in path:
            conversation.append(replies_dict[node])
        longest_conversations.append(conversation)

    conv = longest_conversations

    conversations = []
    for c in conv:
        # 过滤：
        # 1. 评论数小于5的对话
        if len(c) < MIN_DIALOG_LENGTH:
            continue
        temp = []
        for item in c:
            content = item['content']
            if content.startswith('回复 @'):
                content = content.split(':')[1]
            temp.append({
                'from': item['uname'],
                'value': content,
                "video": video_title,
            })
        conversations.append(temp)

    return conversations
