# -*- coding: utf-8 -*-
import requests
import sys
import os
import time
import re
from bs4 import BeautifulSoup

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

def crawl_direct_url(url):
    """直接爬取用户指定的 URL"""
    print(f"  🎯 检测到指定链接，正在定点抓取: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        # 尝试获取主体内容
        content_div = soup.find('article') or soup.find('div', class_='entry-content') or soup.find('body')
        if content_div:
            text = content_div.get_text(separator='\n', strip=True)
            return text[:4000]
    except Exception as e:
        print(f"  ❌ 直接抓取失败: {e}")
    return ""

def crawl_hanchacha(lesson_name):
    """自动搜索 hanchacha.com"""
    print(f"  🔍 正在搜索《{lesson_name}》...")
    all_text = ""
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        search_url = f"https://hanchacha.com/?s={lesson_name}"
        response = requests.get(search_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        found_urls = [link['href'] for link in links if lesson_name.lower() in link.get_text().lower() and 'hanchacha' in link['href']]
        
        for url in list(set(found_urls))[:2]:
            all_text += crawl_direct_url(url) + "\n\n"
    except Exception as e:
        print(f"  自动搜索失败: {e}")
    return all_text[:4000]

def generate_with_ai(lesson_name, raw_materials):
    """调用 AI 生成带【课文原句】的精美笔记"""
    if not DEEPSEEK_API_KEY:
        return generate_fallback_note(lesson_name)
    
    try:
        print("  🤖 正在调用 DeepSeek (严格遵循新表格排版)...")
        prompt = f"""你是小学语文特级教师。请为课文《{lesson_name}》生成排版精美的学霸笔记。

【强制排版要求】
1. 所有表格必须完整填写，绝不能留空。
2. 第三部分“深挖课文宝藏”的表格，必须包含【阅读要点】【课文原句】【写法分析】【写作小技巧】四列！
3. 请严格使用以下 Markdown 结构：

# ✨ {lesson_name} · 学霸笔记

> 💡 学习要点：用反问句引出问题，能激发读者的好奇心。

---

## ✨ 一、课文一瞥：它讲了什么？
（写出核心问题、主要内容、中心句）

---

## ✨ 二、阅读与写作：深挖课文"宝藏"

### 重点段落分析 —— 核心手法
| 阅读要点 | 课文原句 | 写法分析 | 写作小技巧 |
|---|---|---|---|
| 填要点 | 必须填出原文句子 | 分析手法作用 | 教孩子怎么用 |
| 填要点 | 必须填出原文句子 | 分析手法作用 | 教孩子怎么用 |

（请根据课文实际内容，列出2-3个这样的表格）

---

## ✨ 三、语言积累：词语与句式
（归纳词语库和仿写句式）

【参考原始资料】：
{raw_materials[:2500]}
"""
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.4},
            timeout=120
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return generate_fallback_note(lesson_name)
    except:
        return generate_fallback_note(lesson_name)

def generate_fallback_note(lesson_name):
    return f"# {lesson_name}\n\n> ⚠️ AI 调用超时，请稍后重试。"

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    
    # 接收前端传来的合并字符串
    raw_input = sys.argv[1]
    
    # 【核心逻辑】：拆分名字和网址
    if "|||" in raw_input:
        lesson_name, target_url = raw_input.split("|||")
    else:
        lesson_name = raw_input
        target_url = ""
        
    print(f"🕷️ 任务启动: 名称 [{lesson_name}]")
    
    # 如果有指定网址，就直接爬；没有就去搜
    if target_url and target_url.startswith("http"):
        scraped_text = crawl_direct_url(target_url)
    else:
        scraped_text = crawl_hanchacha(lesson_name)
        
    note = generate_with_ai(lesson_name, scraped_text)
    
    os.makedirs('data', exist_ok=True)
    # 文件名依然使用干净的课文名称
    output_file = f"data/{lesson_name}.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(note)

if __name__ == "__main__":
    main()
