# -*- coding: utf-8 -*-
"""
本地服务器端到端测试：
起一个本地小网站，robots.txt 禁止 /secret；
- 抓 /secret 时必须被 robots 拦下，服务器不应收到 /secret 请求；
- 抓 / 时应正常放行并解析出页面。
"""
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QEventLoop
from spider_worker import SpiderWorker

# 记录服务器收到过哪些路径
visited = []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # 关掉默认控制台日志

    def do_GET(self):
        visited.append(self.path)
        if self.path == "/robots.txt":
            body = "User-agent: *\nDisallow: /secret\n".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/":
            body = (
                "<html><head><title>本地站</title></head><body>"
                "<p>首页正文。</p><a href='/about'>关于</a>"
                "</body></html>"
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


server = HTTPServer(("127.0.0.1", 0), Handler)
port = server.server_address[1]

import threading
threading.Thread(target=server.serve_forever, daemon=True).start()

app = QApplication(sys.argv)


def run_worker(url: str):
    """跑一次 worker 线程，阻塞到结束，返回结果字典。"""
    box = {}
    loop = QEventLoop()
    w = SpiderWorker(url, use_cloudscraper=False)
    w.robots_checked.connect(lambda ok, note: box.update(robots=ok, note=note))
    w.page_finished.connect(lambda d: box.update(page=d))
    w.error_occurred.connect(lambda m: box.update(err=m))
    w.finished.connect(loop.quit)
    w.start()
    loop.exec()
    return box


# 第一轮：抓被禁止的 /secret
visited.clear()
blocked = run_worker(f"http://127.0.0.1:{port}/secret")
print("第一轮 /secret robots 允许?", blocked.get("robots"), "|", blocked.get("note"))
print("服务器实际收到的路径:", visited)
assert blocked.get("robots") is False, "robots 应判定 /secret 禁止"
assert "/secret" not in visited, "被禁止路径绝不能发起请求！"
assert "page" not in blocked, "禁止后不应返回页面"

# 第二轮：抓允许的首页
visited.clear()
allowed = run_worker(f"http://127.0.0.1:{port}/")
print("\n第二轮 / robots 允许?", allowed.get("robots"), "|", allowed.get("note"))
print("服务器收到的路径:", visited)
assert allowed.get("robots") is True, "首页应被允许"
assert "page" in allowed, "首页应成功抓取"
print("标题:", allowed["page"]["title"], "| 链接数:", len(allowed["page"]["links"]))
assert allowed["page"]["title"] == "本地站"
assert any(h.endswith("/about") for _, h in allowed["page"]["links"])

server.shutdown()
print("\n✅ robots 禁止即停止 / 允许即抓取 的端到端行为验证通过")
