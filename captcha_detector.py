# -*- coding: utf-8 -*-
"""
captcha_detector.py
===================
人机验证（验证码 / 反机器人挑战）识别模块。

⚠️ 合规边界（重要）
------------------
本模块【只做识别和提示】，不提供、不调用任何“自动解题 / 绕过验证”的能力：
- 不会去点选图片九宫格；
- 不会对接任何收费打码平台；
- 不会伪造验证 token、不会模拟点击通过 reCAPTCHA / hCaptcha / Turnstile。

它的作用是：拿到网页原始 HTML 后，扫描下面这些第三方验证组件在代码里留下的
固定特征（class 名、脚本域名等），判断“这一页用了哪一种人机验证”，
把结果交给界面，由界面用大白话提醒用户：这里需要真人验证，本工具不会自动破解。

目前能识别的四类：
- recaptcha_v2  Google reCAPTCHA v2：“我不是机器人”复选框 / 图片九宫格
- recaptcha_v3  Google reCAPTCHA v3：看不见弹窗，后台纯打分
- hcaptcha      hCaptcha：图片九宫格点选（Discord 注册/登录异常时用的就是它）
- turnstile     Cloudflare Turnstile：无拼图的无痕自动校验

识别只依赖 HTML 文本，不发网络请求，方便单独写单元测试。
"""

# ---------------------------------------------------------------------------
# 识别规则表
# 每条规则：
#   key        稳定标识（界面和语言包用它取名字，不要随便改）
#   markers    在“转成小写后的 HTML”里出现，就判定命中的特征字符串
# ---------------------------------------------------------------------------
_RULES = [
    {
        "key": "recaptcha_v2",
        # 复选框容器 class 最可靠；v2 弹窗 iframe / 后台域名作为补充。
        # 注意：不要在这里放 "recaptcha/api.js"，v3 也会加载同名脚本，避免误判。
        "markers": [
            "g-recaptcha",
            "google.com/recaptcha/enterprise",
            "recaptcha/display",
        ],
    },
    {
        "key": "recaptcha_v3",
        # v3 用 render= 参数加载，页面里调用 grecaptcha.execute 打分
        "markers": [
            "recaptcha/api.js?render=",
            "grecaptcha.execute",
            "grecaptcha.enterprise.execute",
        ],
    },
    {
        "key": "hcaptcha",
        # hCaptcha 容器 class 或它自己的脚本域名（Discord 同款）
        "markers": [
            "h-captcha",
            "hcaptcha.com",
            "js.hcaptcha.com",
        ],
    },
    {
        "key": "turnstile",
        # Cloudflare Turnstile 容器 class 或挑战域名
        "markers": [
            "cf-turnstile",
            "challenges.cloudflare.com/turnstile",
        ],
    },
]


def detect_captcha(html: str) -> list[str]:
    """
    扫描一段网页 HTML，返回命中的人机验证标识列表（可能为空）。

    参数：
        html：网页原始 HTML 文本。

    返回：
        命中的标识 key 列表，例如 ["hcaptcha"]；没有发现任何验证组件时返回 []。
        返回顺序固定按上面规则表的顺序排列，方便界面稳定显示。

    说明：
        - 同一页可能同时出现多种特征（例如 v2 容器和 v3 脚本），会全部列出；
        - 只做字符串特征匹配，不执行页面里的 JavaScript，因此 v3 这种“后台打分、
          页面上看不见控件”的类型，只能靠脚本特征粗略判断；
        - 本函数不修改 HTML、不发起请求、不尝试通过验证。
    """
    if not html:
        return []

    # 统一转小写再匹配，避免 class 大小写差异漏检
    text = html.lower()
    found = []

    for rule in _RULES:
        if any(marker in text for marker in rule["markers"]):
            found.append(rule["key"])

    return found


# 供界面 / 测试直接引用的全部合法标识，便于做完整性检查
KNOWN_KEYS = tuple(rule["key"] for rule in _RULES)
