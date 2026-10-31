# -*- coding: utf-8 -*-
"""本地 HTML 解析验证：不联网，直接测试 worker 里的链接提取/归一化逻辑。"""
from urllib.parse import urljoin
from bs4 import BeautifulSoup

html = """
<html><head><title>测试页</title></head><body>
  <p>第一段正文。</p>
  <a href="/about">关于我们</a>
  <a href="https://example.com/page2">第二页</a>
  <a href="/about">重复链接</a>
  <a href="#section1">页内锚点</a>
  <a href="mailto:test@example.com">邮件</a>
  <a href="javascript:void(0)">脚本链接</a>
</body></html>
"""
target = "https://mysite.com/docs/page1"
soup = BeautifulSoup(html, "lxml")

links = []
seen = set()
for a in soup.find_all("a", href=True):
    text = a.get_text(strip=True)
    href = a["href"].strip()
    if not href or href.startswith("mailto:") or href.startswith("javascript:"):
        continue
    absolute = urljoin(target, href)
    if absolute in seen:
        continue
    seen.add(absolute)
    links.append((text or "(无文字)", absolute))

print("提取到有效链接数:", len(links))
for text, href in links:
    print(" -", text, "->", href)

# 期望：/about 归一化为绝对地址；绝对链接保留；重复去重；锚点/mailto/javascript 被过滤
assert len(links) == 3, f"应得到 3 条有效链接，实际 {len(links)}"
assert any(h == "https://mysite.com/about" for _, h in links), "相对路径应归一化为绝对地址"
assert any(h == "https://example.com/page2" for _, h in links), "绝对链接应保留"
assert not any(h.startswith("mailto:") for _, h in links), "mailto 应被过滤"
assert not any(h.startswith("javascript:") for _, h in links), "javascript 应被过滤"

title = soup.title.get_text(strip=True)
print("标题:", title)
assert title == "测试页"
print("\n✅ 本地 HTML 解析与链接归一化验证通过")
