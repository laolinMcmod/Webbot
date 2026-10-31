# -*- coding: utf-8 -*-
"""
spider_worker.py
================
后台爬虫线程。

为什么要单独一个线程？
PyQt6 界面主线程一旦被网络请求卡住，整个窗口就会“未响应”。所以我们把
“下载 robots.txt、下载网页、解析网页”这一整套耗时操作放进 QThread 后台线程，
做完之后通过 Qt 信号把结果发回主窗口刷新界面。

工作流程（robots.txt 检查为强制步骤，程序里无法关闭）：
1. 规范用户输入的网址（没有 http/https 时自动补 https://）；
2. 无条件先下载网站根目录的 robots.txt，判断目标网址是否允许访问；
3. 如果禁止，就停止并把“被 robots.txt 禁止”的结果回传，绝不再请求目标页面；
4. 如果允许，用 requests 或 cloudscraper（应对 Cloudflare 5 秒盾）下载网页；
5. 用 BeautifulSoup 解析出标题、简介、正文摘要、全部链接；
6. 通过信号把结果发回主窗口。
"""

from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from PyQt6.QtCore import QThread, pyqtSignal

from robots_checker import RobotsTxt
from captcha_detector import detect_captcha
from i18n import t


class SpiderWorker(QThread):
    """后台抓取线程：一次抓取一个网址。"""

    # ---- 自定义信号（主窗口连接这些信号来更新界面）----
    status_changed = pyqtSignal(str)            # 状态文字，显示到状态栏
    robots_checked = pyqtSignal(bool, str)     # robots 结论：(是否允许, 说明文字)
    page_finished = pyqtSignal(dict)           # 页面解析结果字典，发给主窗口展示
    error_occurred = pyqtSignal(str)           # 报错信息

    def __init__(self, url: str, use_cloudscraper: bool, parent=None):
        super().__init__(parent)
        self.raw_url = url.strip()
        # 本程序【强制遵守 robots.txt】，代码里不存在任何跳过检查的开关；
        # 这里只保留是否使用 cloudscraper 应对 Cloudflare 5 秒盾。
        self.use_cloudscraper = use_cloudscraper  # 是否用 cloudscraper 过 CF 盾
        self._cancelled = False                # 手动取消标志

        # 统一的请求头 User-Agent，方便对方站点在 robots.txt 里识别我们
        self.user_agent = RobotsTxt.DEFAULT_UA
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    # 主窗口点“停止”时调用，请求线程尽快结束
    def cancel(self):
        self._cancelled = True

    # ------------------------------------------------------------------
    # 把用户输入规范成完整网址
    # ------------------------------------------------------------------
    @staticmethod
    def normalize_url(raw: str) -> str:
        u = raw.strip()
        if not u:
            return ""
        # 用户只输入了域名，没有写 http/https，自动补上 https://
        if not (u.startswith("http://") or u.startswith("https://")):
            u = "https://" + u
        return u

    # ------------------------------------------------------------------
    # 线程入口函数：run() 会在新线程里自动执行
    # ------------------------------------------------------------------
    def run(self):
        try:
            target = self.normalize_url(self.raw_url)
            if not target:
                self.error_occurred.emit(t("err_no_url"))
                return

            parsed = urlparse(target)
            base = f"{parsed.scheme}://{parsed.netloc}"
            robots_url = base + "/robots.txt"

            # ---------- 第一步：无条件读取并检查 robots.txt ----------
            # 本程序强制遵守 robots.txt，这一步无法关闭；禁止的路径直接停止，不再请求。
            allowed = True
            robots_note = ""

            self.status_changed.emit(t("status_reading_robots", url=robots_url))
            robots = RobotsTxt()
            try:
                r = requests.get(robots_url, headers=self.headers, timeout=15)
                if r.status_code == 200:
                    robots.parse(r.text)
                    allowed = robots.is_allowed(target, self.user_agent)
                    delay = robots.crawl_delay(self.user_agent)
                    if allowed:
                        if delay:
                            robots_note = t("robots_allowed_delay", delay=delay)
                        else:
                            robots_note = t("robots_allowed")
                    else:
                        robots_note = t("robots_blocked")
                elif r.status_code in (401, 403):
                    allowed = False
                    robots_note = t("robots_forbidden_code", code=r.status_code)
                else:
                    # 404 等：网站没有 robots.txt，视为全部允许
                    robots_note = t("robots_missing")
            except requests.RequestException as e:
                robots_note = t("robots_read_fail", err=e)

            self.robots_checked.emit(allowed, robots_note)
            if not allowed:
                self.status_changed.emit(t("status_stopped_by_robots"))
                return

            if self._cancelled:
                return

            # ---------- 第二步：下载目标网页 ----------
            self.status_changed.emit(t("status_downloading"))

            if self.use_cloudscraper:
                # cloudscraper 会模拟浏览器行为，尝试绕过 Cloudflare 5 秒盾
                import cloudscraper
                session = cloudscraper.create_scraper()
            else:
                session = requests.Session()

            resp = session.get(target, headers=self.headers, timeout=20)
            resp.encoding = resp.apparent_encoding or "utf-8"

            if self._cancelled:
                return

            self.status_changed.emit(t("status_download_done", code=resp.status_code))

            # ---------- 第三步：BeautifulSoup 解析 ----------
            soup = BeautifulSoup(resp.text, "lxml")

            # 标题（网页没有 <title> 时用语言包里的兜底文字）
            title = soup.title.get_text(strip=True) if soup.title else t("title_no_title")

            # meta description 简介
            description = ""
            meta = soup.find("meta", attrs={"name": "description"})
            if meta and meta.get("content"):
                description = meta["content"].strip()

            # 正文摘要：收集所有 p 标签文字，拼成一段，截取前 600 字
            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
            body_text = "\n".join(t for t in paragraphs if t)
            summary = body_text[:600] + ("……" if len(body_text) > 600 else "")

            # 全部链接：(链接文字, 绝对地址)
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
                links.append((text or t("link_no_text"), absolute))

            # 识别人机验证组件（只识别、不绕过；识别结果交给界面提示）
            captcha_types = detect_captcha(resp.text)

            result = {
                "url": target,
                "status_code": resp.status_code,
                "title": title,
                "description": description,
                "summary": summary,
                "body_text": body_text,
                "links": links,
                "html": resp.text,
                "robots_note": robots_note,
                "captcha": captcha_types,
            }

            self.status_changed.emit(t("status_parsed"))
            self.page_finished.emit(result)

        except requests.RequestException as e:
            self.error_occurred.emit(t("err_network", err=e))
        except Exception as e:  # 兜底，避免后台线程静默崩溃
            self.error_occurred.emit(t("err_generic", name=type(e).__name__, err=e))
