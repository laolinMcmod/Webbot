# -*- coding: utf-8 -*-
"""联网集成测试：真实抓取 example.com，验证 robots 检查 + 下载 + 解析全流程。"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QEventLoop
from spider_worker import SpiderWorker

app = QApplication(sys.argv)

worker = SpiderWorker("https://example.com", use_cloudscraper=False)
box = {}
loop = QEventLoop()

worker.status_changed.connect(lambda s: print("状态:", s))
worker.robots_checked.connect(lambda ok, note: (box.update(robots=ok, note=note), print("robots:", ok, "|", note)))
worker.page_finished.connect(lambda d: box.update(page=d))
worker.error_occurred.connect(lambda m: (box.update(err=m), print("错误:", m)))
worker.finished.connect(loop.quit)

worker.start()
loop.exec()

if "err" in box:
    print("❌ 抓取失败：", box["err"]); sys.exit(1)

page = box["page"]
print("\n===== 抓取结果 =====")
print("最终网址:", page["url"])
print("状态码:", page["status_code"])
print("标题:", page["title"])
print("简介:", page["description"] or "(无)")
print("链接数量:", len(page["links"]))
for text, href in page["links"][:5]:
    print("  -", text, "->", href)
print("正文摘要前 120 字:", page["summary"][:120])
print("原始 HTML 字符数:", len(page["html"]))

# 基本断言
assert page["status_code"] == 200, "状态码应为 200"
assert "Example Domain" in page["title"], "标题应为 Example Domain"
assert box.get("robots") is True, "example.com 应允许抓取"
assert page["html"].strip(), "原始 HTML 源码不能为空"
print("\n✅ 联网集成测试通过")
