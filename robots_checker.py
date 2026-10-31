# -*- coding: utf-8 -*-
"""
robots_checker.py
=================
负责抓取并解析网站根目录的 robots.txt，并判断某个网址允许不允许我们访问。

规则依据：RFC 9309《Robots Exclusion Protocol》
- 按 User-agent（用户代理）分成若干组；
- 一个空行表示“上一组到此结束”，后面的 user-agent 属于新组；
- 路径规则是“前缀匹配”，规则末尾带 $ 表示必须精确匹配到结尾；
- 同一条网址命中多条规则时，规则文本更长（更具体）的优先；
  如果允许(Allow)和禁止(Disallow)的长度一样，Allow 优先；
- User-agent 比较时只取“产品名”（product token，斜杠、空格之前的第一段，转小写）；
  规则里写 * 表示通配所有爬虫；
- 网站没有 robots.txt、网络失败或返回 404 时，默认“全部允许”。

本文件只做纯文本解析和判断，不直接发网络请求；网络抓取交给爬虫线程。
"""

from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# 单条路径规则：例如 Allow: /public/  或  Disallow: /private/$
# ---------------------------------------------------------------------------
class _Rule:
    """一条 Allow 或 Disallow 规则。"""

    __slots__ = ("is_allow", "pattern", "anchored_end")

    def __init__(self, is_allow: bool, pattern: str, anchored_end: bool):
        self.is_allow = is_allow          # True=允许(Allow)，False=禁止(Disallow)
        self.pattern = pattern            # 去掉 $ 之后的规则文本
        self.anchored_end = anchored_end  # 原规则末尾是否带 $（结尾锚定）


# ---------------------------------------------------------------------------
# 解析好的一组规则：对应 robots.txt 里一个或多个 User-agent 共用的那一段
# ---------------------------------------------------------------------------
class _Group:
    """一组规则：里面有一组 User-agent 和它们共用的 Allow/Disallow。"""

    __slots__ = ("agents", "rules", "crawl_delay")

    def __init__(self):
        self.agents = set()        # 这一组覆盖哪些爬虫 UA（产品名，小写）
        self.rules = []            # 这一组的路径规则列表 [_Rule]
        self.crawl_delay = None    # Crawl-delay 秒数（没有就为 None）


class RobotsTxt:
    """解析一段 robots.txt 文本，并对外提供 is_allowed(url) 判断。"""

    # 我们自己对外使用的默认爬虫名字（会写在请求头 User-Agent 里）
    DEFAULT_UA = "PythonWebRobot/1.0 (+local educational crawler)"

    def __init__(self, text: str = ""):
        self._groups = []          # 全部规则组
        self._default_group = None  # 对应 User-agent: * 的那一组
        if text:
            self.parse(text)

    # ------------------------------------------------------------------
    # 工具方法：从完整 User-Agent 字符串里取出“产品名”（product token）
    # 例如 "PythonWebRobot/1.0 (+xxx)" -> "pythonwebrobot"
    # ------------------------------------------------------------------
    @staticmethod
    def product_token(user_agent: str) -> str:
        ua = (user_agent or "*").strip().lower()
        # 先按空格、括号、斜杠切开，取第一段
        token = ua.split(" ", 1)[0]
        token = token.split("/", 1)[0]
        token = token.split("(", 1)[0]
        return token or "*"

    # ------------------------------------------------------------------
    # 解析 robots.txt 全文
    # ------------------------------------------------------------------
    def parse(self, text: str) -> None:
        self._groups.clear()
        self._default_group = None
        current = None  # 当前正在填充的那一组；遇到空行就置回 None

        for raw_line in text.splitlines():
            # 去掉注释（# 之后的内容全部丢弃）和首尾空白
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                # 空行：结束当前分组
                current = None
                continue

            # 按第一个冒号分成“字段名”和“值”
            if ":" not in line:
                continue
            field, _, value = line.partition(":")
            field = field.strip().lower()
            value = value.strip()

            if field == "user-agent":
                # 新的 UA 行：如果当前组已经写过 Allow/Disallow，就另起一组
                if current is None or current.rules:
                    current = _Group()
                    self._groups.append(current)
                current.agents.add(self.product_token(value))

            elif field in ("allow", "disallow"):
                if current is None:
                    # 规则写在任何 UA 之前时，补建一个默认组
                    current = _Group()
                    self._groups.append(current)
                # 空的 Allow/Disallow（例如 Disallow: ）表示“不限制”，忽略
                if value:
                    anchored_end = value.endswith("$")
                    pattern = value[:-1] if anchored_end else value
                    current.rules.append(_Rule(
                        is_allow=(field == "allow"),
                        pattern=pattern,
                        anchored_end=anchored_end,
                    ))

            elif field == "crawl-delay":
                if current is not None:
                    try:
                        current.crawl_delay = float(value)
                    except ValueError:
                        current.crawl_delay = None

            # sitemap、其他字段这里不需要处理，直接忽略

        # 找出 User-agent: * 的默认组
        for g in self._groups:
            if "*" in g.agents:
                self._default_group = g
                break

    # ------------------------------------------------------------------
    # 在某一组里，判断给定路径是否被允许
    # ------------------------------------------------------------------
    def _path_allowed(self, group: _Group, path: str) -> bool:
        # 找出所有“命中”当前路径的规则
        matched = []
        for rule in group.rules:
            if self._rule_matches(rule, path):
                matched.append(rule)

        if not matched:
            # 没有任何规则命中 = 允许访问
            return True

        # 最具体（pattern 最长）的规则胜出
        matched.sort(key=lambda r: len(r.pattern), reverse=True)
        winner = matched[0]
        return winner.is_allow

    # ------------------------------------------------------------------
    # 判断单条规则是否命中某条路径
    # ------------------------------------------------------------------
    @staticmethod
    def _rule_matches(rule: _Rule, path: str) -> bool:
        pattern = rule.pattern
        # 空规则不产生限制（解析阶段已过滤，这里兜底）
        if not pattern:
            return True

        if rule.anchored_end:
            # 结尾带 $：路径必须和规则完全相等
            return path == pattern

        # 规则里支持 * 通配任意字符；先按通配符切成普通片段做前缀/包含判断
        # RFC 常见用法是前缀匹配，这里同时支持 * 通配。
        if "*" not in pattern:
            # 纯前缀匹配
            return path.startswith(pattern)

        # 把 pattern 里的 * 当通配，用 fnmatch 思路：转成正则
        import re
        regex = "^"
        for ch in pattern:
            if ch == "*":
                regex += ".*"
            else:
                regex += re.escape(ch)
        regex += "$"
        return re.match(regex, path) is not None

    # ------------------------------------------------------------------
    # 对外主接口：判断某个完整 URL 是否允许抓取
    # ------------------------------------------------------------------
    def is_allowed(self, url: str, user_agent: str = DEFAULT_UA) -> bool:
        parsed = urlparse(url)
        path = parsed.path or "/"
        # robots 规则只针对路径，不针对查询参数
        if not path.startswith("/"):
            path = "/" + path

        token = self.product_token(user_agent)

        # 1) 先找声明了我们这个 UA 的专属组
        group = None
        for g in self._groups:
            if token in g.agents:
                group = g
                break

        # 2) 找不到专属组，就用 User-agent: * 默认组
        if group is None:
            group = self._default_group

        # 3) 连默认组都没有（robots.txt 里只声明了别的 UA），等于不限制
        if group is None:
            return True

        return self._path_allowed(group, path)

    # ------------------------------------------------------------------
    # 读取 Crawl-delay（没有就返回 None）
    # ------------------------------------------------------------------
    def crawl_delay(self, user_agent: str = DEFAULT_UA):
        token = self.product_token(user_agent)
        for g in self._groups:
            if token in g.agents:
                return g.crawl_delay
        if self._default_group:
            return self._default_group.crawl_delay
        return None
