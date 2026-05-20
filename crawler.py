# -*- coding: utf-8 -*-
import requests
import sys
import os
import re
from bs4 import BeautifulSoup

# 从环境变量中获取 API Key
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

def crawl_direct_url(url):
    """直接爬取用户指定的 URL"""
    print(f"  🎯 正在定点抓取链接: {url}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.find('article') or soup.find('div', class_='entry-content') or soup.find('body')
        if content_div:
            return content_div.get_text(separator='\n', strip=True)[:4000]
    except Exception as e:
        print(f"  ❌ 直接抓取失败: {e}")
    return ""

def crawl_hanchacha(lesson_name):
    """如果没给链接，则自动搜索 hanchacha.com"""
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
        print(f"  ❌ 自动搜索失败: {e}")
    return all_text[:4000]

def generate_with_ai(lesson_name, raw_materials):
    """调用 DeepSeek 生成笔记"""
    # 诊断性输出
    if not DEEPSEEK_API_KEY:
        print("  ❌ 致命错误：完全没有读到 DEEPSEEK_API_KEY！请检查 GitHub Actions 的 Secrets 配置。")
        return f"# {lesson_name}\n\n> ⚠️ 找不到 API 钥匙，请检查 GitHub Secrets 配置。"
    else:
        print(f"  ✅ 成功读到 KEY，前4位是: {DEEPSEEK_API_KEY[:4]}****")
    
    try:
        print("  🤖 正在调用 DeepSeek API...")
        prompt = f"""你是小学语文特级教师。请为课文《{lesson_name}》生成排版精美的学霸笔记。

【强制排版要求】
1. 所有表格必须完整填写，绝不能留空。
2. 第三部分“深挖课文宝藏”的表格，必须包含【阅读要点】【课文原句】【写法分析】【写作小技巧】四列！
3. 请使用 Markdown 格式：

# ✨ {lesson_name} · 学霸笔记

> 💡 学习要点：归纳文章核心艺术特色。

---

## ✨ 一、课文一瞥：它讲了什么？
（简要写出核心问题、主要内容、中心句）

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
            print("  ✅ AI 生成成功！")
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"  ❌ DeepSeek 拒绝请求！状态码: {response.status_code}")
            print(f"  ❌ 详细原因: {response.text}")
            return f"# {lesson_name}\n\n> ⚠️ AI 报错！状态码 {response.status_code}，请查看 GitHub Actions 黑框日志。"
            
    except Exception as e:
        print(f"  ❌ 网络异常崩溃: {e}")
        return f"# {lesson_name}\n\n> ⚠️ 请求报错: {e}"

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    
    raw_input = sys.argv[1]
    
    # 拆分名称和网址
    if "|||" in raw_input:
        lesson_name, target_url = raw_input.split("|||")
    else:
        lesson_name = raw_input
        target_url = ""
        
    print(f"🕷️ 任务启动: 名称 [{lesson_name}]")
    
    if target_url and target_url.startswith("http"):
        scraped_text = crawl_direct_url(target_url)
    else:
        scraped_text = crawl_hanchacha(lesson_name)
        
    note = generate_with_ai(lesson_name, scraped_text)
    
    # 【文件名清洗】：防止特殊字符导致创建文件失败
    clean_name = re.sub(r'[\\/*?:"<>|]', "_", lesson_name)
    os.makedirs('data', exist_ok=True)
    output_file = f"data/{clean_name}.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(note)
    print(f"✅ 文件已保存: {output_file}")

if __name__ == "__main__":
    main()
