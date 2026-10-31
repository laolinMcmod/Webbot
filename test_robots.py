# -*- coding: utf-8 -*-
r"""
test_robots.py
==============
robots_checker.py 的规则单元测试。
在虚拟环境里运行：
    .venv\Scripts\python.exe test_robots.py
全部通过会打印 “全部测试通过 ✅”。
"""

from robots_checker import RobotsTxt


def check(name: str, actual: bool, expected: bool):
    status = "✅" if actual == expected else "❌"
    print(f"{status} {name}: 期望={expected} 实际={actual}")
    assert actual == expected, f"用例失败：{name}"


# 1. 前缀匹配：Disallow: /private/
r = RobotsTxt(
    "User-agent: *\n"
    "Disallow: /private/\n"
)
check("前缀：/private/secret 禁止", r.is_allowed("https://x.com/private/secret"), False)
check("前缀：/public/secret 允许", r.is_allowed("https://x.com/public/secret"), True)

# 2. 结尾锚定 $：Disallow: /private$
r = RobotsTxt(
    "User-agent: *\n"
    "Disallow: /private$\n"
)
check("$锚定：/private 禁止", r.is_allowed("https://x.com/private"), False)
check("$锚定：/private/x 允许（子路径不受影响）", r.is_allowed("https://x.com/private/x"), True)

# 3. 空行结束分组：A 只禁 /a，B 只禁 /b
r = RobotsTxt(
    "User-agent: AlphaBot\n"
    "Disallow: /a\n"
    "\n"
    "User-agent: BetaBot\n"
    "Disallow: /b\n"
)
check("分组：Alpha 访问 /a 禁止", r.is_allowed("https://x.com/a", "AlphaBot/1.0"), False)
check("分组：Alpha 访问 /b 允许", r.is_allowed("https://x.com/b", "AlphaBot/1.0"), True)
check("分组：Beta 访问 /b 禁止", r.is_allowed("https://x.com/b", "BetaBot/2.0"), False)
check("分组：Beta 访问 /a 允许", r.is_allowed("https://x.com/a", "BetaBot/2.0"), True)

# 4. UA 产品名匹配：规则写 MyBot，请求 MyBot/1.0 应命中
r = RobotsTxt(
    "User-agent: MyBot\n"
    "Disallow: /secret\n"
)
check("UA产品名：MyBot/1.0 命中专属组", r.is_allowed("https://x.com/secret", "MyBot/1.0"), False)

# 5. 更具体的 Allow 胜出
r = RobotsTxt(
    "User-agent: *\n"
    "Disallow: /folder\n"
    "Allow: /folder/public\n"
)
check("Allow更具体：/folder/public 允许", r.is_allowed("https://x.com/folder/public"), True)
check("Allow更具体：/folder/private 禁止", r.is_allowed("https://x.com/folder/private"), False)

# 6. 通配符 *：禁止所有 /xxx/admin 形式
r = RobotsTxt(
    "User-agent: *\n"
    "Disallow: /*/admin\n"
)
check("通配：/site/admin 禁止", r.is_allowed("https://x.com/site/admin"), False)
check("通配：/site/other 允许", r.is_allowed("https://x.com/site/other"), True)

# 7. 空 robots.txt：全部允许
r = RobotsTxt("")
check("空文件：任意路径允许", r.is_allowed("https://x.com/anything"), True)

# 8. 只声明了别的爬虫，我们没被列出：默认允许
r = RobotsTxt(
    "User-agent: Googlebot\n"
    "Disallow: /google-only\n"
)
check("未声明本UA：默认允许", r.is_allowed("https://x.com/google-only"), True)

# 9. Crawl-delay 读取
r = RobotsTxt(
    "User-agent: *\n"
    "Crawl-delay: 3\n"
)
check("Crawl-delay 读到 3 秒", r.crawl_delay() == 3.0, True)

print("\n全部测试通过 ✅")
