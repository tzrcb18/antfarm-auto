# -*- coding: utf-8 -*-
import os
import requests
import re

WECOM_KEY = os.getenv("WECOM_WEBHOOK_KEY")
URL_LIST = [
    "https://app.ali213.net/gl/562127.html"
]

def remove_html_tags(text):
    """删除全部html标签，只保留文字"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def send_wechat_text(title, content):
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
        # 第一步：剥离所有HTML标签，拿到纯净文本
        pure_text = remove_html_tags(html)
        # 多行模式，宽松匹配【日期】，后面抓取两行问答，问号分割题目答案
        pattern = re.compile(r"【(\d+\.\d+)】.*?([^？]+？)(\w+).*?([^？]+？)(\w+)", re.S)
        result = pattern.search(pure_text)
        if result:
            date_str = result.group(1).strip()
            q1 = result.group(2).strip()
            ans1 = result.group(3).strip()
            q2 = result.group(4).strip()
            ans2 = result.group(5).strip()
            out_text = f"📅 {date_str}\n1. {q1}\n✅答案：{ans1}\n\n2. {q2}\n✅答案：{ans2}"
            return out_text
        else:
            print(f"页面{url}访问成功，纯文本解析后，未匹配问答")
            # 调试：输出前1200字符纯文本，方便排查
            print("页面纯文本片段：", pure_text[:1200])
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
        send_wechat_text("【蚂蚁庄园任务告警】", "页面解析失败，请检查页面结构")
