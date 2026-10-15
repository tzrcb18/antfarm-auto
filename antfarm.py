# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')
import os
import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# ========== 配置区 ==========
WECOM_KEY = os.getenv("WECOM_WEBHOOK_KEY")
URL_LIST = [
    "https://app.ali213.net/gl/562127.html",
    "https://www.duotegame.com/mgl/25944.html",
    "https://www.caochai.cn/myzy/",
]
SCREENSHOT_RAW = "screenshot_raw.png"
SCREENSHOT_COMPRESS = "screenshot.jpg"
# ============================

def is_valid_image(file_path):
    """校验图片是否有效，过滤空白/0字节损坏图片"""
    if not os.path.exists(file_path):
        return False
    if os.path.getsize(file_path) < 2000: #小于2KB判定为空空白截图
        print(f"⚠️图片过小，判定为空白截图，跳过，大小：{os.path.getsize(file_path)}")
        return False
    try:
        with Image.open(file_path) as im:
            im.verify()
        return True
    except Exception as e:
        print(f"⚠️图片文件损坏：{e}")
        return False

def compress_img(in_path, out_path, max_w=900, quality=70):
    img = Image.open(in_path)
    w, h = img.size
    if w > max_w:
        new_h = int(h * max_w / w)
        img = img.resize((max_w, new_h))
    img.save(out_path, "JPEG", quality=quality)
    return out_path

def send_wecom_msg(img_path=None, fail_msg:str=None):
    webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WECOM_KEY}"
    if fail_msg:
        payload = {
            "msgtype":"markdown",
            "markdown":{"content":f"**蚂蚁庄园任务告警**\n{fail_msg}"}
        }
        resp = requests.post(webhook_url, json=payload)
        print("告警推送结果：",resp.text)
        return

    upload_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key={WECOM_KEY}&type=image"
    # 修复：直接打开文件句柄，不要f.read()
    with open(img_path, "rb") as f:
        files_data = {
            "media": ("screenshot.jpg", f, "image/jpeg")
        }
        r_upload = requests.post(upload_url, files=files_data)
    res_upload = r_upload.json()
    print("素材上传返回：", res_upload)
    if res_upload.get("errcode") !=0:
        send_wecom_msg(fail_msg=f"图片上传失败:{res_upload}")
        return False
    media_id = res_upload["media_id"]
    send_data = {"msgtype":"image","image":{"media_id":media_id}}
    r = requests.post(webhook_url, json=send_data)
    print("图片推送结果：", r.text)
    return True

def capture_page(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=800,1300")
    driver = None
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        driver.set_page_load_timeout(20)
        print(f"正在访问页面: {url}")
        driver.get(url)
        driver.implicitly_wait(10)
        driver.save_screenshot(SCREENSHOT_RAW)
        # 校验原始截图是否有效
        if not is_valid_image(SCREENSHOT_RAW):
            print(f"❌页面 {url} 截图是空白无效图，跳过")
            return None
        compress_img(SCREENSHOT_RAW, SCREENSHOT_COMPRESS)
        print(f"✅ {url} 截图压缩完成")
        return SCREENSHOT_COMPRESS
    except Exception as e:
        print(f"❌访问 {url} 出错:{str(e)}")
        return None
    finally:
        if driver:
            driver.quit()
        if os.path.exists(SCREENSHOT_RAW):
            os.remove(SCREENSHOT_RAW)

if __name__ == "__main__":
    if not WECOM_KEY:
        print("❌未读取环境变量 WECOM_WEBHOOK_KEY，请检查仓库Secret配置")
        sys.exit(1)

shot_file = None
for target_url in URL_LIST:
    shot_file = capture_page(target_url)
    if shot_file:
        #二次校验压缩后图片
        if is_valid_image(shot_file):
            break
        else:
            shot_file = None

if shot_file:
    send_wecom_msg(img_path=shot_file)
    if os.path.exists(shot_file):
        os.remove(shot_file)
else:
    err_text = "全部站点截图失败，GitHub海外IP大概率被目标网站拦截，页面返回空白"
    print(err_text)
    send_wecom_msg(fail_msg=err_text)
