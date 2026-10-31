# -*- coding: utf-8 -*-
r"""
test_captcha.py
===============
captcha_detector.py 的离线单元测试：不联网，只喂一段模拟 HTML，
检查四类人机验证特征能不能被正确认出，普通页面不会误报。

运行方式：
    .venv\Scripts\python.exe test_captcha.py
"""

from captcha_detector import detect_captcha, KNOWN_KEYS


def check(name: str, actual: list, expected: list):
    """对比识别结果和期望结果，不一致就报错退出。"""
    ok = actual == expected
    mark = "✅" if ok else "❌"
    print(f"{mark} {name}: 期望={expected} 实际={actual}")
    if not ok:
        raise AssertionError(f"用例失败：{name}")


# 1. 空页面 / 空字符串：不识别出任何组件
check("空字符串返回空列表", detect_captcha(""), [])
check("普通静态页面不误报", detect_captcha(
    "<html><head><title>Hello</title></head><body><p>普通文字</p></body></html>"
), [])

# 2. Google reCAPTCHA v2：复选框容器 class
check(
    "识别 reCAPTCHA v2（g-recaptcha 容器）",
    detect_captcha('<div class="g-recaptcha" data-sitekey="6Lxxxx"></div>'),
    ["recaptcha_v2"],
)

# 3. Google reCAPTCHA v3：带 render= 的脚本 + execute 调用
check(
    "识别 reCAPTCHA v3（render 脚本）",
    detect_captcha(
        '<script src="https://www.google.com/recaptcha/api.js?render=6Lxxxx"></script>'
        "<script>grecaptcha.execute('6Lxxxx', {action:'login'})</script>"
    ),
    ["recaptcha_v3"],
)

# 4. hCaptcha：Discord 同款图片点选组件
check(
    "识别 hCaptcha（h-captcha 容器）",
    detect_captcha('<div class="h-captcha" data-sitekey="xxxx"></div>'),
    ["hcaptcha"],
)

# 5. Cloudflare Turnstile：无痕校验容器
check(
    "识别 Cloudflare Turnstile（cf-turnstile 容器）",
    detect_captcha('<div class="cf-turnstile" data-sitekey="xxxx"></div>'),
    ["turnstile"],
)

# 6. 大小写不敏感：class 写成大写也能认出
check(
    "大小写不敏感（H-CAPTCHA 大写）",
    detect_captcha('<DIV CLASS="H-CAPTCHA" DATA-SITEKEY="x"></DIV>'),
    ["hcaptcha"],
)

# 7. 同一页同时出现多种特征，按规则顺序全部列出
both = detect_captcha(
    '<div class="g-recaptcha" data-sitekey="a"></div>'
    '<div class="h-captcha" data-sitekey="b"></div>'
)
check("同一页同时出现 v2 与 hCaptcha", both, ["recaptcha_v2", "hcaptcha"])

# 8. 规则表覆盖的标识和界面映射使用的标识一致，防止漏登记
assert set(KNOWN_KEYS) == {
    "recaptcha_v2", "recaptcha_v3", "hcaptcha", "turnstile"
}, "已知验证标识列表与预期不一致"

print("\n全部人机验证识别测试通过 ✅")
