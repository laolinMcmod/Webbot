# -*- coding: utf-8 -*-
"""
i18n.py
=======
国际化（Internationalization，简称 i18n）文字包。

什么是 i18n？
------------
把“显示给用户看的所有文字”从界面代码里抽出来，统一放到本文件的语言字典里。
界面上不直接写死中文，而是调用 t("文字编号") 去取当前语言对应的句子。
以后想加一门新语言（比如日语、繁体中文），只要在下面 _STRINGS 里再加一份字典，
不用去改 main.py、spider_worker.py 里的界面代码。

本文件提供三个最常用的函数：
- set_language(语言代码)：切换当前语言；
- current_language()：读取当前语言代码；
- t(文字编号, 占位符=值)：取当前语言的一句话，支持 {xxx} 占位符填进动态内容。

支持的语言在 LANGUAGES 里登记，下拉框就是照着它生成的。
"""

# ---------------------------------------------------------------------------
# 支持的语言表：左边是语言代码（程序内部用），右边是下拉框里显示给用户看的名字
# 想新增语言，先在这里加一行，再到下面 _STRINGS 里补一份对应字典即可。
# ---------------------------------------------------------------------------
LANGUAGES = {
    "zh": "简体中文",
    "en": "English",
}

# ---------------------------------------------------------------------------
# 所有界面文字都集中在这张大表里。
# 结构：_STRINGS[语言代码][文字编号] = 一句话
# 文字编号（key）统一用英文蛇形命名，例如 "start_btn"、"status_ready"。
# 句子里需要动态填内容的地方，用 {占位符} 表示，例如 "状态码 {code}"。
# ---------------------------------------------------------------------------
_STRINGS = {

    # ===================== 简体中文（默认语言，新手友好大白话） =====================
    "zh": {
        # ---- 窗口标题 ----
        "app_title": "网页爬虫工具（强制遵守 robots.txt · 内置浏览器预览）",

        # ---- 顶部网址栏 ----
        "url_label": "网址：",
        "url_placeholder": "例如：https://example.com  （输完按回车就能抓取）",
        "start_btn": "开始抓取",
        "stop_btn": "停止",

        # ---- 第二行选项 ----
        "robots_lock": "🔒 本程序强制遵守 robots.txt（不可关闭）",
        "cf_check": "开启防拦截模式（遇到打不开的网站再勾）",
        "cf_tooltip": "有些网站装了反爬保护（常见叫 Cloudflare 5 秒盾），勾上后会模拟浏览器去请求；普通、能正常打开的网站不用勾。",
        "language_label": "语言：",

        # ---- 右侧选项卡标题 ----
        "tab_info": "网页信息",
        "tab_links": "链接列表",
        "tab_html": "HTML 源代码",

        # ---- “网页信息”选项卡 ----
        "body_summary_label": "正文摘要：",
        "title_prefix": "标题：{title}",
        "title_no_title": "(无标题)",
        "desc_prefix": "简介：{desc}",
        "no_description": "简介：（网页没有写简介）",
        "no_body": "（没能提取到正文内容）",
        "robots_prefix": "robots.txt：{note}",

        # ---- “HTML 源代码”选项卡 ----
        "html_meta_empty": "尚未抓取网页，暂时没有源码",
        "html_meta_filled": "共 {lines} 行，{chars} 字符（原始 HTML，没有做任何修改）",
        "save_html_btn": "另存为 .html 文件",
        "save_dialog_filter": "网页文件 (*.html *.htm)",
        "save_success": "HTML 源码已保存：{path}",

        # ---- 状态栏默认提示 ----
        "status_ready": "就绪：输入网址后，点“开始抓取”。",
        "status_busy_title": "正在抓取 …",
        "status_stopping": "正在停止 …",
        "status_error": "出错了",

        # ---- 弹窗标题与提示 ----
        "warn_no_url_title": "提示",
        "warn_no_url": "请先输入要抓取的网址！",
        "info_no_html_title": "提示",
        "info_no_html": "还没有可保存的网页源码，请先抓取网页。",
        "save_fail_title": "保存失败",
        "save_fail": "写文件时出错：{err}",
        "crawl_fail_title": "抓取失败",

        # ---- 后台线程状态文字（spider_worker.py 使用）----
        "status_reading_robots": "正在读取 {url} …",
        "robots_allowed": "robots.txt 检查通过，允许抓取",
        "robots_allowed_delay": "robots.txt 检查通过，允许抓取（网站建议两次之间间隔 {delay} 秒）",
        "robots_blocked": "robots.txt 禁止抓取这个路径，已按规则停止",
        "robots_forbidden_code": "robots.txt 返回 {code}，按保守原则不抓取",
        "robots_missing": "网站没有 robots.txt（或读不到），视为允许抓取",
        "robots_read_fail": "读取 robots.txt 失败（{err}），按默认允许继续",
        "status_stopped_by_robots": "已经按照 robots.txt 的规则停止抓取。",
        "status_downloading": "正在下载网页 …",
        "status_download_done": "网页下载完成，状态码 {code}，正在解析 …",
        "status_parsed": "解析完成 ✅",
        "status_done": "抓取完成：{url}  状态码 {code}，一共 {n} 个链接。",
        "err_no_url": "请先输入要抓取的网址！",
        "err_network": "网络请求出错：{err}",
        "err_generic": "程序出错：{name}: {err}",
        "link_no_text": "(没有文字)",

        # ---- 人机验证识别提示（只提示，不绕过、不破解）----
        "captcha_section_label": "人机验证检测：",
        "captcha_none": "本页未检测到常见人机验证组件。",
        "captcha_warning": "⚠ 本工具只做识别，不会自动点选图片、不会绕过人机验证；需要真人操作的页面请在浏览器里手动完成。",
        "captcha_recaptcha_v2": "Google reCAPTCHA v2（“我不是机器人”复选框 / 图片九宫格）",
        "captcha_recaptcha_v3": "Google reCAPTCHA v3（后台自动打分，页面上看不到弹窗）",
        "captcha_hcaptcha": "hCaptcha（图片九宫格点选，Discord 注册/登录同款）",
        "captcha_turnstile": "Cloudflare Turnstile（无痕自动校验，没有拼图）",
    },

    # ===================== English（基础英文，方便切换演示） =====================
    "en": {
        # ---- Window title ----
        "app_title": "Web Crawler (robots.txt enforced · built-in browser preview)",

        # ---- Top URL bar ----
        "url_label": "URL:",
        "url_placeholder": "e.g. https://example.com  (press Enter to crawl)",
        "start_btn": "Start",
        "stop_btn": "Stop",

        # ---- Options row ----
        "robots_lock": "🔒 robots.txt is enforced and cannot be turned off",
        "cf_check": "Anti-blocking mode (check only if a site won't open)",
        "cf_tooltip": "Some sites use anti-bot protection (Cloudflare 5-second challenge). Check this to send browser-like requests. Leave it off for normal sites.",
        "language_label": "Language:",

        # ---- Right-side tabs ----
        "tab_info": "Page Info",
        "tab_links": "Links",
        "tab_html": "HTML Source",

        # ---- "Page Info" tab ----
        "body_summary_label": "Summary:",
        "title_prefix": "Title: {title}",
        "title_no_title": "(no title)",
        "desc_prefix": "Description: {desc}",
        "no_description": "Description: (none provided by the page)",
        "no_body": "(no body text could be extracted)",
        "robots_prefix": "robots.txt: {note}",

        # ---- "HTML Source" tab ----
        "html_meta_empty": "No page crawled yet, no source code",
        "html_meta_filled": "{lines} lines, {chars} characters (raw HTML, unchanged)",
        "save_html_btn": "Save as .html",
        "save_dialog_filter": "Web page (*.html *.htm)",
        "save_success": "HTML source saved: {path}",

        # ---- Status bar ----
        "status_ready": "Ready: type a URL and click Start.",
        "status_busy_title": "Crawling …",
        "status_stopping": "Stopping …",
        "status_error": "Error",

        # ---- Message boxes ----
        "warn_no_url_title": "Notice",
        "warn_no_url": "Please enter a URL first!",
        "info_no_html_title": "Notice",
        "info_no_html": "No source code to save yet. Crawl a page first.",
        "save_fail_title": "Save failed",
        "save_fail": "Error writing file: {err}",
        "crawl_fail_title": "Crawl failed",

        # ---- Background worker status ----
        "status_reading_robots": "Reading {url} …",
        "robots_allowed": "robots.txt check passed, allowed to crawl",
        "robots_allowed_delay": "robots.txt check passed, allowed (site suggests a {delay}-second delay)",
        "robots_blocked": "robots.txt forbids this path, stopped by the rules",
        "robots_forbidden_code": "robots.txt returned {code}, staying on the safe side and not crawling",
        "robots_missing": "No robots.txt (or unreadable), treated as allowed",
        "robots_read_fail": "Failed to read robots.txt ({err}), continuing with default allow",
        "status_stopped_by_robots": "Stopped according to robots.txt rules.",
        "status_downloading": "Downloading the page …",
        "status_download_done": "Page downloaded, status code {code}, parsing …",
        "status_parsed": "Parsing done ✅",
        "status_done": "Done: {url}  status {code}, {n} links found.",
        "err_no_url": "Please enter a URL first!",
        "err_network": "Network request error: {err}",
        "err_generic": "Program error: {name}: {err}",
        "link_no_text": "(no text)",

        # ---- Captcha detection notice (detect only; never bypass or solve) ----
        "captcha_section_label": "Bot check detected:",
        "captcha_none": "No common bot-check component found on this page.",
        "captcha_warning": "⚠ This tool only detects challenges. It never clicks images or bypasses bot checks; complete any human check manually in a real browser.",
        "captcha_recaptcha_v2": "Google reCAPTCHA v2 (\"I'm not a robot\" checkbox / image grid)",
        "captcha_recaptcha_v3": "Google reCAPTCHA v3 (background score, no visible popup)",
        "captcha_hcaptcha": "hCaptcha (image grid, same as Discord signup/login)",
        "captcha_turnstile": "Cloudflare Turnstile (invisible auto-check, no puzzle)",
    },
}

# 当前使用的语言代码，默认简体中文
_current_lang = "zh"


def set_language(lang: str) -> None:
    """切换当前语言。传进来的代码不在语言表里时，保持原语言不变。"""
    global _current_lang
    if lang in _STRINGS:
        _current_lang = lang


def current_language() -> str:
    """返回当前语言代码（"zh" 或 "en"）。"""
    return _current_lang


def t(key: str, **kwargs) -> str:
    """
    取当前语言里编号为 key 的那句话。

    - 找不到编号时，先退回中文，再找不到就把编号本身返回，方便排查漏写；
    - 传进来的关键字参数会填进句子里的 {占位符}，例如 t("status_done", code=200)。
    """
    table = _STRINGS.get(_current_lang, {})
    text = table.get(key)
    if text is None:
        text = _STRINGS["zh"].get(key, key)

    # 有占位符参数时做格式化；占位符缺失也不报错，原样保留句子
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text
