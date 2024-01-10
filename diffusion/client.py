import requests


def call_diffusion_gen(server: str = "http://127.0.0.1:8080", prompt: str = ""):
    # /grgbrain/chat
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json'
    }
    url = f"{server}/diffusion/gen"
    r = requests.get(url, params={
        "prompt": prompt,
    }, headers=headers)
    return r.json()


if __name__ == "__main__":
    res = call_diffusion_gen(prompt="cat play in glass")
    print(res)