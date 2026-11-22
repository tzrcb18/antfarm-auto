# -*- coding: utf-8 -*-
import os
import time
import requests
import re
from bs4 import BeautifulSoup

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


def get_all_answers(url):
    """解析页面所有【MM.DD】日期块，按页面顺序（新→旧）返回问答列表"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        pure_text = soup.get_text(separator="\n")
        print("页面文本片段:\n", pure_text[:3000])

        block_pattern = re.compile(r"【(\d+\.\d+)】")
        blocks = block_pattern.split(pure_text)
        result = []
        # blocks 结构: ["前缀文本", "11.13", "块内容", "11.12", "块内容", ...]
        for i in range(1, len(blocks), 2):
            date_str = blocks[i].strip()
            block_content = blocks[i + 1].strip()
            qa_pat = re.compile(r"(.*？)\s*([^\n]+)")
            qa_list = qa_pat.findall(block_content)
            qa_list = [(q.strip(), a.strip()) for q, a in qa_list
                       if q.strip() and a.strip()]
            if len(qa_list) >= 2:
                result.append({
                    "date": date_str,
                    "q1": qa_list[0][0],
                    "ans1": qa_list[0][1],
                    "q2": qa_list[1][0],
                    "ans2": qa_list[1][1]
                })
        print("页面解析到的日期顺序（从上到下=由新到旧）：",
              [x["date"] for x in result])
        return result
    except Exception as e:
        print(f"访问/解析异常: {str(e)}")
        return []


def load_sent_dates():
    sent = set()
    if os.path.exists(FLAG_FILE):
        with open(FLAG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if s:
                    sent.add(s)
    return sent


def save_sent_dates(sent_set):
    with open(FLAG_FILE, "w", encoding="utf-8") as f:
        for d in sent_set:
            f.write(d + "\n")


if __name__ == "__main__":
    sent_dates = load_sent_dates()

    if not WECOM_KEY:
        send_wechat_text("配置错误", "仓库Secret WECOM_WEBHOOK_KEY未填写")
        exit(1)

    all_items = []
    for link in URL_LIST:
        items = get_all_answers(link)
        time.sleep(1)
        all_items.extend(items)

    if len(all_items) == 0:
        send_wechat_text("【蚂蚁庄园任务告警】", "页面解析失败，没有抓到任何问答块")
        exit(1)

    # 只取页面最新的 2 条（列表前两位）
    latest_two = all_items[:2]
    print(f"选中页面最新两条日期：{[x['date'] for x in latest_two]}")

    # 过滤掉当天已经推送过的日期
    need_push = []
    new_sent = set(sent_dates)
    for it in latest_two:
        d = it["date"]
        if d not in sent_dates:
            need_push.append(it)
            new_sent.add(d)

    # 两条都已经推送过 → 当天任务视为已完成，后续触发直接跳过，不发消息
    if len(need_push) == 0:
        print("✅ 最新两天答案均已推送过，本次跳过，等待第二天页面更新")
        exit(0)

    msg_parts = []
    for it in need_push:
        block = (
            f"📅 {it['date']}\n"
            f"1. {it['q1']}\n✅答案：{it['ans1']}\n\n"
            f"2. {it['q2']}\n✅答案：{it['ans2']}\n"
            "——————————\n"
        )
        msg_parts.append(block)
    final_msg = "\n".join(msg_parts)

    send_wechat_text("【蚂蚁庄园 最新答案】", final_msg)
    save_sent_dates(new_sent)
    print(f"✅推送完成，标记已写入本地flag，新增日期："
          f"{[x['date'] for x in need_push]}")
    exit(0)
