# 网页爬虫工具（强制遵守 robots.txt · 内置浏览器预览 · 中英双语）

一个用 **Python + PyQt6** 写的桌面图形界面爬虫工具。程序会**无条件、强制**先读取网站的
`robots.txt`，按规则判断允不允许抓取；**禁止的路径直接停下、绝不请求**；允许了才下载网页，
用内置的 **WebEngine 浏览器内核**在左侧预览，右侧同时给出网页信息、链接列表和**原始 HTML 源代码**
（可以另存为本地 `.html` 文件）。界面自带 **简体中文 / English 双语切换**。

---

## 一、怎么启动（最简单：双击）

1. 打开项目文件夹
2. **双击 `run.bat`**
3. 稍等几秒钟，就会弹出程序窗口。

如果 `run.bat` 打不开，也可以用命令行手动启动：

```powershell
# 先创建虚拟环境并安装依赖（只需第一次）
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

# 启动程序
.\.venv\Scripts\python.exe main.py
```

---

## 二、界面上每个东西是干什么的（新手导览）

| 位置 | 名称 | 作用（大白话） |
|------|------|------|
| 顶部输入框 | 网址 | 粘贴要抓取的网址，也可以只填域名（会自动补 `https://`），按回车等于点“开始抓取” |
| 按钮 | 开始抓取 | 先检查 robots.txt → 下载网页 → 解析 → 左侧预览、右侧显示结果 |
| 按钮 | 停止 | 抓取中途想停下来时点它 |
| 绿色提示 | 🔒 强制遵守 robots.txt | **这是写死的规矩，不能关掉**。只要网站不允许，程序就不会去抓 |
| 勾选框 | 开启防拦截模式 | 遇到打不开、被网站拦住的网站再勾；普通能正常打开的网站不用勾 |
| 下拉框 | 语言 | 在「简体中文」和「English」之间切换，按钮和提示文字会立刻变 |
| 左侧大区域 | 网页预览 | 内置浏览器内核，把刚刚抓到的网页渲染出来给你看 |
| 右侧「网页信息」 | 标题 / 简介 / 正文摘要 | 从网页里解析出来的主要文字内容 |
| 右侧「网页信息」 | 人机验证检测 | 自动认出这页有没有挂 reCAPTCHA / hCaptcha / Turnstile 这类验证组件，只做提示，**不会自动去点图或绕过** |
| 右侧「链接列表」 | 全部链接 | 页面上所有可用链接，**双击某一条**会直接去抓那个链接 |
| 右侧「HTML 源代码」 | 原始 HTML | 抓到的前端网页**原始代码**，一个字都没改过；顶部显示行数和字符数，可点“另存为 .html 文件”保存到本地 |
| 最底部 | 状态栏 | 实时显示当前进度和结果提示 |

### 三个新手容易懵的小词，先提前认识一下

- **robots.txt**：网站放在自己根目录的一张“访客规矩表”，写明哪些路径允许爬虫看、哪些禁止。程序开头一定会先去读它。
- **HTML 源代码**：浏览器背后真正收到的网页文件（一堆标签和文字），左侧是它渲染出来的样子，右侧“HTML 源代码”选项卡就是原始文件本身。
- **Cloudflare 5 秒盾（防拦截模式）**：有些网站会先弹出一个几秒的“检查你是不是机器人”的页面，勾选防拦截模式后会模拟浏览器去请求；实在绕不过去就说明网站拒绝访问，应当尊重、不要反复重试。

---

## 三、文件结构（每个脚本是干嘛的）

```
webrobot_py/
├── main.py                # 【程序入口】图形界面主窗口，双击 run.bat 实际跑的就是它
├── spider_worker.py       # 后台爬虫线程：下载 robots、下载网页、解析标题/正文/链接
├── robots_checker.py      # robots.txt 解析器：判断某个网址允许不允许抓取
├── captcha_detector.py    # 人机验证识别器：只认出页面挂了哪种验证组件，不绕过、不解题
├── i18n.py                # 【国际化语言包】集中放中/英文案，切换语言都从这里取词
├── test_robots.py         # robots 规则单元测试
├── test_captcha.py        # 人机验证识别单元测试
├── verify_parse.py        # 本地 HTML 解析与链接归一化测试
├── server_test.py         # 本地服务器端到端测试：验证“禁止就停、允许才抓”
├── integration_test.py    # 真实联网测试：抓取 example.com
├── smoke_test.py          # 界面构造 + 语言切换冒烟测试
├── requirements.txt       # 已经锁定好的第三方库版本清单
└── run.bat                # 双击启动脚本（Windows）
```

### 各模块分工一句话说清

- **robots_checker.py**：只负责“读规则、判允许”，不发网络请求，方便单独测试。
  规则遵循 RFC 9309：前缀匹配、规则末尾 `$` 表示必须匹配到结尾、按 User-agent 分组、
  空行结束一组、Allow 与 Disallow 同长时 Allow 优先。
- **spider_worker.py**：跑在后台线程里，所以下载网页时**界面不会卡死**。做完一步就用
  Qt 信号通知主窗口刷新；所有给用户看的状态、提示文字都从 `i18n.py` 取词。
- **main.py**：只负责画界面、接收后台线程发回来的结果并显示；切换语言时调用
  `_retranslate_ui()` 把外壳文字刷新成新语言。
- **i18n.py**：所有界面文案集中在 `_STRINGS` 字典里，一个编号对应一句中文、一句英文。
- **captcha_detector.py**：拿到网页 HTML 后只做特征扫描，判断页面挂了哪一种人机验证；
  它不执行页面脚本、不点击、不解题，识别结果交给界面做合规提示。

---

## 四、国际化（i18n）是怎么组织的，以后怎么加一门新语言

### 现在的工作方式

1. `i18n.py` 顶部 `LANGUAGES` 登记支持的语言：代码和显示名，例如 `"zh": "简体中文"`。
2. `_STRINGS` 里每种语言一份字典，键是统一的编号（如 `start_btn`），值是那句话。
3. 代码里不写死文字，而是调用 `t("start_btn")` 取当前语言的句子；需要填动态内容时用
   占位符，例如 `t("status_done", code=200, n=5)`。
4. 下拉框切换语言时，`main.py` 调用 `set_language()` 改当前语言，再刷新界面外壳文字。

> 注意：已经抓到的网页标题、正文、源码是网站**原始内容**，程序不翻译；翻译的只是程序自己的按钮、标签、提示。

### 想新增一门语言（比如日语、繁体中文）怎么做

1. 打开 `i18n.py`，在 `LANGUAGES` 里加一行，例如：
   ```python
   "ja": "日本語",
   ```
2. 在 `_STRINGS` 里再复制一份字典，把所有编号句子翻译成日语（编号一个都不能少）。
3. 保存后重新运行程序，下拉框里就会出现新语言；`smoke_test.py` 会自动按语言数量检查下拉框条目。

---

## 五、运行自带测试（想验证程序没坏时用）

在项目文件夹里打开 PowerShell，依次执行：

```powershell
# 1. robots 规则单元测试
.\.venv\Scripts\python.exe test_robots.py

# 2. 人机验证识别单元测试
.\.venv\Scripts\python.exe test_captcha.py

# 3. 本地 HTML 解析测试
.\.venv\Scripts\python.exe verify_parse.py

# 4. 本地服务器端到端测试（禁止即停止）
.\.venv\Scripts\python.exe server_test.py

# 5. 真实联网测试
.\.venv\Scripts\python.exe integration_test.py

# 6. 界面构造 + 语言切换测试
.\.venv\Scripts\python.exe smoke_test.py
```

全部通过时都会打印“✅ ……通过”，最后一个测试会打印 `SMOKE OK`。

---

## 六、已经装好的第三方库（版本已锁定）

见 `requirements.txt`，主要包括：

- `PyQt6` / `PyQt6-WebEngine`：图形界面和内置浏览器内核
- `requests`：发送普通网页请求
- `cloudscraper`：应对 Cloudflare 5 秒盾
- `beautifulsoup4` + `lxml`：解析 HTML、提取标题正文和链接
- `robotexclusionrulesparser`：备用的 robots 解析参考库

> 备注：本程序实际判断逻辑写在 `robots_checker.py` 里，规则清晰可读、方便学习。

---

## 七、人机验证（验证码）科普：Discord 用的是哪一种

### 1. 先记住结论：Discord 用的是 hCaptcha

Discord 在**注册账号、手机验证、登录异常**时弹出的图片九宫格点选验证，用的是第三方服务商 **hCaptcha**（不是 Discord 自己写的）；少数历史或异常场景也可能加载 Google reCAPTCHA。hCaptcha 的样子就是：给你几张小图，要求点出所有交通灯、自行车、船只之类的物体。

### 2. 现在网上常见的四类人机验证

| 类型 | 用户看到的样子 | 网页代码里的识别特征 | 常见场景 |
|------|----------------|----------------------|----------|
| **Google reCAPTCHA v2** | “我不是机器人”复选框，点完可能跳图片九宫格 | `class="g-recaptcha"`、`data-sitekey`、`google.com/recaptcha` | 网站注册、留言、登录 |
| **Google reCAPTCHA v3** | 页面上**看不见**任何弹窗，后台纯打分（0.0 机器人～1.0 真人） | 脚本 `recaptcha/api.js?render=`、`grecaptcha.execute(...)` | 风控、防刷接口 |
| **hCaptcha** | 图片九宫格点选（**Discord 同款**） | `class="h-captcha"`、`hcaptcha.com` | Discord、GitHub 异常登录、部分交易所 |
| **Cloudflare Turnstile** | 无拼图、无痕自动校验，不弹题目 | `class="cf-turnstile"`、`challenges.cloudflare.com/turnstile` | 新一代无验证码防护 |

> 小知识：`data-sitekey` 这个属性名 reCAPTCHA、hCaptcha、Turnstile 都会用，**不能**靠它判断是哪一家；真正区分要靠上面的 class 名和脚本域名，`captcha_detector.py` 就是按这个思路识别的。

### 3. 本工具对人机验证的态度：只识别、绝不绕过

- 程序下载页面后，`captcha_detector.py` 只扫描上面这些**静态特征**，判断这页挂了哪一种验证，然后在右侧「网页信息」里用橙色文字告诉你类型，并附上合规提示。
- 本工具**不提供、也不会去做**下面这些事：自动点选图片、对接收费打码平台、伪造验证 token、模拟点击通过 reCAPTCHA / hCaptcha / Turnstile，更不会批量注册账号。这些属于绕过网站访问控制、违反对方服务条款的行为。
- 勾选“开启防拦截模式”用到的 `cloudscraper`，只能应对 Cloudflare 那种“5 秒盾”静态/JS 跳转，**它解不了图片九宫格验证码**；遇到需要真人点图的页面，请在真实浏览器里手动完成。
- 登录、注册、发消息这类**需要人机验证和账号身份**的操作，本来就不是一个学习型静态网页爬虫该做的事。

---

## 八、常见问题

**1. 启动后网页预览一片空白？**
先看右侧“网页信息”和底部状态栏有没有提示。如果是 robots 禁止或网络错误，会在状态栏和红色提示里写出来。

**2. 某个网站提示被 robots.txt 禁止？**
这是正常的保护行为：程序遵守网站规矩，自动停下，不会绕过去。换一个允许抓取的练习站点即可。

**3. 某个网站提示被 Cloudflare 拦住？**
勾选“开启防拦截模式”再试。个别很强的反爬措施 cloudscraper 也可能绕不过，这属于网站主动拒绝访问，应尊重对方，不要反复重试。

**4. 想把抓到的网页源码保存成文件？**
切到右侧「HTML 源代码」选项卡，点顶部“另存为 .html 文件”，选一个位置保存即可，保存的就是原始 HTML。

**5. 下载很慢 / 超时？**
程序超时设为 15～20 秒。国内访问境外站点本来就可能慢，换一个国内站点试试。

**6. 控制台弹出 `WSALookupServiceBegin 10108`、`iCCP`、几行 `js:` 警告？**
这些是内置 Chromium 内核和被访问网站前端打印的**无害提示**，和本程序代码无关，不影响抓取和预览；程序启动时已把内核日志级别调到最高，正常运行时不会再刷出大量红字。

**7. 想重新安装依赖（换电脑或环境坏了）？**
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

---

## 九、可以拿来练习的网站（robots 允许学习抓取）

- `https://example.com` —— 最简单的测试页，第一次上手先用它
- `https://books.toscrape.com` —— 模拟书店，有分页、分类、价格
- `https://quotes.toscrape.com` —— 名言网站，带标签和作者
- `https://scrapethissite.com` —— 表格、分页、表单练习
- `https://web-scraping.dev` —— 专门测试 robots、延时和链接陷阱

---

## 十、重要提醒（请务必遵守）

1. **robots.txt 是网站的抓取规矩，本程序强制遵守、无法关闭**，这是设计要求。
2. 本工具只用于**学习 Python 网络编程和网页结构**，不要高频、批量抓取别人的网站，避免给对方服务器造成负担。
3. 抓取受版权保护的内容时，请遵守网站条款和法律法规，仅做个人学习参考。
4. 部分网站禁止任何爬虫访问，程序会自动停下，这是正常保护行为。
5. **遇到人机验证（reCAPTCHA / hCaptcha / Turnstile）时，本工具只做识别提示，不会也不能自动破解；需要真人操作的页面请手动在浏览器里完成。**
