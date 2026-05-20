# -*- coding: utf-8 -*-
import requests
import sys
import os
import time
import re
from bs4 import BeautifulSoup

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

def crawl_hanchacha(lesson_name):
    """从 hanchacha.com 爬取所有相关资料"""
    print(f"  🔍 正在从 hanchacha.com 搜索《{lesson_name}》...")
    all_text = ""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        search_url = f"https://hanchacha.com/?s={lesson_name}"
        response = requests.get(search_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=True)
        found_urls = []
        
        for link in links:
            href = link.get('href', '')
            text = link.get_text().lower()
            if lesson_name.lower() in text and 'hanchacha.com' in href:
                if href not in found_urls:
                    found_urls.append(href)
        
        print(f"    找到 {len(found_urls)} 个相关页面")
        
        for url in found_urls[:3]:
            try:
                page_resp = requests.get(url, headers=headers, timeout=15)
                page_soup = BeautifulSoup(page_resp.text, 'html.parser')
                content_div = page_soup.find('article') or page_soup.find('div', class_='entry-content')
                if content_div:
                    text = content_div.get_text(strip=True)
                    text = re.sub(r'\s+', ' ', text)
                    all_text += f"\n\n---\n{text[:1500]}"
            except:
                continue
    except Exception as e:
        print(f"  hanchacha 爬取失败: {e}")
    
    return all_text[:4000]

def generate_with_ai(lesson_name, raw_materials):
    """使用 AI 生成详细的学霸笔记"""
    if not DEEPSEEK_API_KEY:
        print("  ⚠️ 警告: 未配置 DEEPSEEK_API_KEY，启用优雅备用模板")
        return generate_fallback_note(lesson_name, raw_materials)
    
    try:
        print("  🤖 正在调用 DeepSeek API (已配置超时宽容时间)...")
        prompt = f"""你是小学语文特级教师。请为课文《{lesson_name}》生成一份超级详细、排版精美的学霸笔记。

【重要要求】
1. 必须完全填充所有的内容，每个表格都要填满，绝对不能留空，更不能写“请根据课文填写”。
2. 结合给出的参考资料，如果没有参考资料，请根据你自身强大的语文大模型知识库进行合理而专业的教学输出。
3. 严格遵循下述 Markdown 模板输出。

请按以下格式输出：

# 🌊 探秘{lesson_name} · 学霸综合笔记 🐠

> 一份集**知识点、课堂笔记、教学思路**于一体的超实用手册

---

## 📚 一、课文一瞥：它讲了什么？

* **核心问题**：本文主要探讨了什么？
* **主要内容**：请在这里写下200字左右的高质量课文核心内容串联。
* **中心句**：写出课文最核心的点睛之句。

---

## 🧱 二、文章结构：总分总，超清晰！

| 部分 | 自然段 | 内容 | 作用 |
|------|--------|------|------|
| 开头 | 填具体自然段 | 描写了什么 | 起到什么作用 |
| 中间 | 填具体自然段 | 描写了什么 | 起到什么作用 |
| 结尾 | 填具体自然段 | 描写了什么 | 照应开头/总结全文 |

> 💡 **写作要点：** 归纳总结本文的结构艺术。

---

## ✨ 三、阅读与写作：深挖课文"宝藏"

### 写作特色分析

| 阅读要点 | 写法分析 | 写作小技巧 |
|----------|----------|------------|
| 关键特色1 | 结合课文具体分析 | 孩子可以学到的应用技巧 |
| 关键特色2 | 结合课文具体分析 | 孩子可以学到的应用技巧 |

---

## 📝 四、语言积累：词语库+句式库

### 重点词语
| 类别 | 词语 |
|------|------|
| 必会字词 | 词语1, 词语2, 词语3 |
| 近义词 | 词语A-词语B |
| 反义词 | 词语C-词语D |
| 成语/AABC | 比如四字成语等 |

### 仿写句式
> **修辞手法与句式运用**
> * **课文原句**：写出原句
> * **仿写示例**：写出高水平的仿写

---

## 🎯 五、课后挑战：小试牛刀
1. **朗读小能手**：设计一个具体的朗读任务。
2. **小小解说员**：复述或演说任务。
3. **妙笔生花**：小练笔要求。

【参考原始资料】：
{raw_materials[:2500]}
"""
        # 注意：调高了 timeout 到 120 秒，避免 AI 因为思考导致连接断开
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是小学语文特级教师，极度擅长输出详实的 Markdown 课文硬核笔记。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5, # 稍微调低随机性，让结构更稳固
                "max_tokens": 4000
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            note = result["choices"][0]["message"]["content"]
            print(f"  ✅ AI 生成成功！字数: {len(note)}")
            return note
        else:
            print(f"  ⚠️ AI 失败状态码: {response.status_code}")
            return generate_fallback_note(lesson_name, raw_materials)
    except Exception as e:
        print(f"  ⚠️ AI 异常: {e}")
        return generate_fallback_note(lesson_name, raw_materials)

def generate_fallback_note(lesson_name, raw_materials):
    """
    优雅的骨架备用模板：
    即使网络崩了、AI断了，也返回标准的Markdown结构和空表格，
    让前端漂亮地渲染出来，方便用户手动在 Obsidian 里填空。
    """
    return f"""# 📖 {lesson_name} · 学习笔记 (标准骨架版)

> ⚠️ 提示：云端 AI 调度遇到波峰延时，已自动为您开启「结构精简版」笔记。

---

## 📚 一、课文一瞥：它讲了什么？

* **核心问题**：本文的核心线索是什么？
* **主要内容**：请通读课文《{lesson_name}》后尝试用一句话概括。
* **中心句**：寻找文中开门见山或篇末点题的句子。

---

## 🧱 二、文章结构：总分总，超清晰！

| 部分 | 自然段 | 内容 | 作用 |
|------|--------|------|------|
| 开头 | 1 | 引入课文主体 | 激发兴趣，开门见山 |
| 中间 | 2 ~ 结束前 | 分述不同维度特点 | 详实描写，展开核心 |
| 结尾 | 篇末最后 | 总结深化主体 | 总结全文，余音绕梁 |

---

## 📝 三、语言积累：词语库+句式库

### 重点词语
| 类别 | 预习推荐归纳栏 |
|------|------|
| 必会字词 | 请从《{lesson_name}》课后生字表中摘录 |
| 近义词 | 寻找文中的高频形容词并查阅近义词 |
| 反义词 | 寻找对应词语 |

---

*自动避堵生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}*
"""

def main():
    if len(sys.argv) < 2:
        print("请提供课文名称")
        sys.exit(1)
    
    lesson_name = sys.argv[1]
    print("=" * 50)
    print(f"🕷️ 正在开启云端作业：生成《{lesson_name}》...")
    hanchacha_text = crawl_hanchacha(lesson_name)
    note = generate_with_ai(lesson_name, hanchacha_text)
    
    os.makedirs('data', exist_ok=True)
    output_file = f"data/{lesson_name}.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(note)
    print(f"✅ 文件安全写入: {output_file}")

if __name__ == "__main__":
    main()
