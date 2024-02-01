import sys
import time
from urllib.parse import urlparse, parse_qs

import qrcode_terminal
from bilibili_api import LoginError, Credential

import os
from bs4 import BeautifulSoup as soup
from bilibili_api.login import API, parse_credential_url
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
import logging

from selenium.webdriver.support.wait import WebDriverWait
import base64
from PIL import Image
from io import BytesIO
from pyzbar.pyzbar import decode


def login_bilibili():
    url = "https://www.bilibili.com/"
    # 打开网页
    logging.getLogger("selenium").setLevel(logging.CRITICAL)
    options = ChromeOptions()
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"
    )
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    proxy = os.getenv("http_proxy")
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    # 找到登录按扭进行点击操作
    driver.find_element(By.CLASS_NAME, "go-login-btn").click()

    # 等待新页面加载完成
    time.sleep(5)
    # 解析二维码
    scan = driver.find_element(By.CLASS_NAME, "login-scan-box")
    scan_status_url = scan.find_element(By.TAG_NAME, "div").find_element(By.TAG_NAME, "div").get_attribute("title")
    parsed_url = urlparse(scan_status_url)
    params = parse_qs(parsed_url.query)
    qrcode_key = params.get('qrcode_key', [''])[0]

    img_base64_string = scan.find_element(By.TAG_NAME, "img").get_attribute("src")
    image_data = base64.b64decode(img_base64_string.replace("data:image/png;base64,", ""))
    image = Image.open(BytesIO(image_data))
    decocdeQR = decode(image)
    qrcode_terminal.draw(decocdeQR[0].data.decode('ascii'))

    while True:
        events_api = API["qrcode"]["get_events"]
        event_url = events_api["url"] + f"?qrcode_key={qrcode_key}&source=main-fe-header"
        driver.get(event_url)
        page_source = driver.execute_script("return document.body.outerHTML;")
        page_soup = soup(page_source, "html.parser")
        body = page_soup.find_all("body")[0].text
        events = eval(body)

        if "code" in events.keys() and events["code"] == 0:
            if events["data"]["code"] == 86101:
                sys.stdout.write("请用bilibili客户端扫描二维码↑\n")
                sys.stdout.flush()
            elif events["data"]["code"] == 86090:
                sys.stdout.write("点下确认啊！\n")
                sys.stdout.flush()
            elif events["data"]["code"] == 86038:
                print("二维码过期，请扫新二维码！\n")
                return login_bilibili()
            elif events["data"]["code"] == 0:
                sys.stdout.write("登录成功！\n")
                sys.stdout.flush()
                cookies = parse_credential_url(events).get_cookies()
                return cookies
            elif "code" in events.keys():
                raise LoginError(events["message"])
        time.sleep(2)


if __name__ == '__main__':
    credential_cookies = login_bilibili()
    print(credential_cookies)
