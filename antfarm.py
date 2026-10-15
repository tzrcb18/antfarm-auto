# -*- coding: utf-8 -*-
import os
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

WECOM_KEY = os.getenv("WECOM_WEBHOOK_KEY")
URL_LIST = [
    "https://app.ali213.net/gl/562127.html"
]
FLAG_FILE = "flag.txt"

def send_wechat_text(title, content):
    webhook = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WECOM_KEY}"
    msg = {
        "msgtype": "text",
        "text": {
            "content": f"{title}\n{content}"
        }
    }
    res = requests.post(webhook, json=msg)
    print("推送返回：", res.json())
    return res.json()

def get_answer(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = "utf-8"
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")
        pure_text = soup.get_text(separator="\n")
        print("页面纯文本:\n", pure_text[:1500])

        pattern = re.compile(r"【(\d+\.\d+)】\s*(.*?？)\s*(\w+)\s*(.*?？)\s*(\w+)", re.S)
        match = pattern.search(pure_text)
        if match:
            date_str = match.group(1).strip()
            q1 = match.group(2).strip()
            ans1 = match.group(3).strip()
            q2 = match.group(4).strip()
            ans2 = match.group(5).strip()
            out_text = f"📅 {date_str}\n1. {q1}\n✅答案：{ans1}\n\n2. {q2}\n✅答案：{ans2}"
            return out_text
        else:
            print("未匹配问答")
            return None
    except Exception as e:
        print(f"访问异常: {str(e)}")
        return None

if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")
    # 读取标记文件
    flag_today = None
    if os.path.exists(FLAG_FILE):
        with open(FLAG_FILE, "r", encoding="utf-8") as f:
            flag_today = f.read().strip()

    if flag_today == today:
        print(f"✅今日{today}已经推送成功，本次跳过执行")
        exit(0)

    # 没有标记，正常执行爬虫
    if not WECOM_KEY:
        send_wechat_text("配置错误", "仓库Secret WECOM_WEBHOOK_KEY未填写")
        exit(1)
    final_content = None
    for link in URL_LIST:
        final_content = get_answer(link)
        if final_content:
            break
    if final_content:
        send_wechat_text("【蚂蚁庄园每日答案】", final_content)
        # 推送成功！写入当日标记文件
        with open(FLAG_FILE, "w", encoding="utf-8") as f:
            f.write(today)
        print(f"✅已写入今日标记 {today}")
    else:
        send_wechat_text("【蚂蚁庄园任务告警】", "页面解析失败，请检查页面结构")
