import requests
from bilibili_api import search


def call_bilibili_crawl(server: str = "http://127.0.0.1:7070", query: str = ""):
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json'
    }
    response = requests.get(
        url=f"{server}/bilibili_crawl/run",
        params={"query": query},
        headers=headers
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    res = call_bilibili_crawl(query="极氪007")
    print(res)
