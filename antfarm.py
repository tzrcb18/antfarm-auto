# -*- coding: utf-8 -*-
import os
import requests
import re

WECOM_KEY = os.getenv("WECOM_WEBHOOK_KEY")
# 优先游侠网链接，备用多特
URL_LIST = [
    "https://app.ali213.net/gl/562127.html",
    "https://www.duotegame.com/mgl/25944.html"
]

def send_wechat_text(title, content):
    """企业微信机器人推送markdown文字"""
    webhook = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WECOM_KEY}"
    msg = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"## {title}\n{content}"
        }
    }
    res = requests.post(webhook, json=msg)
    print("推送返回：", res.json())

def get_answer(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text

        # 匹配【日期】后面的两组问答，游侠网页面专用正则
        pattern = re.compile(r"【(\d+\.\d+)】\s*(.*?\？)\s*(\w+)\s*(.*?\？)\s*(\w+)", re.S)
        result = pattern.search(html)
        if result:
            date_str = result.group(1).strip()
            q1 = result.group(2).strip()
            ans1 = result.group(3).strip()
            q2 = result.group(4).strip()
            ans2 = result.group(5).strip()
            out_text = f"📅 {date_str}\n1. {q1}\n✅答案：{ans1}\n\n2. {q2}\n✅答案：{ans2}"
            return out_text
        else:
            print(f"页面{url}访问成功，但是没有匹配到问答内容")
            return None
    except Exception as e:
        print(f"访问 {url} 失败: {str(e)}")
        return None

if __name__ == "__main__":
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
    else:
        send_wechat_text("【蚂蚁庄园任务告警】", "所有网页抓取失败，GitHub海外IP被拦截或者页面解析失败")
