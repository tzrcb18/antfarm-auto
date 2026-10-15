# -*- coding: utf-8 -*-
import os
import requests
import re

WECOM_KEY = os.getenv("WECOM_WEBHOOK_KEY")
# 备选网页列表
URL_LIST = [
    "https://www.duotegame.com/mgl/25944.html",
    "https://app.ali213.net/gl/562127.html"
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

        # 正则匹配题目和答案（根据多特游戏网页适配）
        pattern_q = re.compile(r"题目[:：](.*?)答案[:：]([A-D])", re.S)
        result = pattern_q.search(html)
        if result:
            question = result.group(1).strip()
            ans = result.group(2).strip()
            return f"**题目**：{question}\n**答案：{ans}**"
        else:
            print(f"页面{url}找到页面，但没有匹配到答案")
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
        send_wechat_text("【蚂蚁庄园任务告警】", "所有网页抓取失败，GitHub海外IP被拦截")
