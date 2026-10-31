# -*- coding: utf-8 -*-
r"""
main.py
=======
强制遵守 robots.txt 的 PyQt6 桌面爬虫工具（内置浏览器预览 + HTML 源代码面板 + 中英双语）。

这是程序入口，直接运行本文件即可打开图形界面：
    .venv\Scripts\python.exe main.py

界面组成：
- 顶部：网址输入框 + “开始抓取”按钮 + “停止”按钮；
- 选项：robots.txt 强制遵守（不可关闭，仅显示提示）；防拦截模式开关；语言下拉框（中/英）；
- 左侧：QWebEngineView 内置浏览器内核，预览抓到的网页；
- 右侧三个选项卡：网页信息（标题、简介、robots 结论、正文摘要）、链接列表、HTML 源代码（原始前端 HTML，可另存为 .html 文件）；
- 底部：状态栏，实时显示当前进度。

抓取动作在后台线程（spider_worker.py）里完成，界面不会卡死。
所有界面文案统一来自 i18n.py 语言包。
"""

import os
import sys
from urllib.parse import urlparse

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QCheckBox, QSplitter, QLabel, QListWidget,
    QListWidgetItem, QTextEdit, QTabWidget, QStatusBar, QMessageBox, QFileDialog,
    QComboBox,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

from spider_worker import SpiderWorker
from i18n import t, LANGUAGES, set_language

# 识别模块返回的验证标识 -> i18n 语言包编号（新增类型时两边一起补）
CAPTCHA_I18N_KEY = {
    "recaptcha_v2": "captcha_recaptcha_v2",
    "recaptcha_v3": "captcha_recaptcha_v3",
    "hcaptcha": "captcha_hcaptcha",
    "turnstile": "captcha_turnstile",
}


class MainWindow(QMainWindow):
    """主窗口。"""

    def __init__(self):
        super().__init__()
        self.worker = None  # 当前后台爬虫线程
        self._build_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # 1) 搭建界面
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.setWindowTitle(t("app_title"))
        self.resize(1280, 820)

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(8)

        # ---- 第一行：网址输入 + 按钮 ----
        bar = QHBoxLayout()
        self.url_label = QLabel(t("url_label"))
        bar.addWidget(self.url_label)
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText(t("url_placeholder"))
        self.url_edit.returnPressed.connect(self.start_crawl)
        bar.addWidget(self.url_edit, 1)

        self.start_btn = QPushButton(t("start_btn"))
        self.start_btn.setMinimumWidth(100)
        self.stop_btn = QPushButton(t("stop_btn"))
        self.stop_btn.setMinimumWidth(80)
        self.stop_btn.setEnabled(False)
        bar.addWidget(self.start_btn)
        bar.addWidget(self.stop_btn)
        root_layout.addLayout(bar)

        # ---- 第二行：选项（robots 强制提示 + 防拦截开关 + 语言切换）----
        options = QHBoxLayout()
        # robots.txt 为强制遵守：程序不提供任何关闭开关，这里只用标签固定提示
        self.robot_lock_label = QLabel(t("robots_lock"))
        self.robot_lock_label.setStyleSheet("color:#2c6e2c; font-weight:bold;")
        self.cf_check = QCheckBox(t("cf_check"))
        self.cf_check.setChecked(True)
        self.cf_check.setToolTip(t("cf_tooltip"))
        options.addWidget(self.robot_lock_label)
        options.addSpacing(24)
        options.addWidget(self.cf_check)
        options.addStretch(1)

        # 语言切换下拉框：选项来自 i18n.LANGUAGES，切换后刷新整窗文案
        self.language_label = QLabel(t("language_label"))
        self.lang_combo = QComboBox()
        for code, name in LANGUAGES.items():
            self.lang_combo.addItem(name, code)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        options.addWidget(self.language_label)
        options.addWidget(self.lang_combo)
        root_layout.addLayout(options)

        # ---- 中间：左右分栏 ----
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧：网页预览内核
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("about:blank"))
        splitter.addWidget(self.browser)

        # 右侧：结果选项卡
        right = QTabWidget()

        # 选项卡一：网页信息
        info_page = QWidget()
        info_layout = QVBoxLayout(info_page)
        self.title_label = QLabel("")
        self.title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.title_label.setWordWrap(True)
        self.robot_label = QLabel("")
        self.robot_label.setWordWrap(True)
        self.robot_label.setStyleSheet("color: #2c6e2c;")
        # 人机验证识别结果标签（只提示，不绕过）
        self.captcha_label = QLabel("")
        self.captcha_label.setWordWrap(True)
        self.captcha_label.setStyleSheet("color: #b26a00;")
        self.desc_label = QLabel("")
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #555;")
        self.body_summary_label = QLabel(t("body_summary_label"))
        self.body_edit = QTextEdit()
        self.body_edit.setReadOnly(True)
        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.robot_label)
        info_layout.addWidget(self.captcha_label)
        info_layout.addWidget(self.desc_label)
        info_layout.addWidget(self.body_summary_label)
        info_layout.addWidget(self.body_edit)
        self.info_tab = right.addTab(info_page, t("tab_info"))

        # 选项卡二：链接列表
        link_page = QWidget()
        link_layout = QVBoxLayout(link_page)
        self.link_list = QListWidget()
        self.link_list.itemDoubleClicked.connect(self._open_link)
        link_layout.addWidget(self.link_list)
        self.link_tab = right.addTab(link_page, t("tab_links"))

        # 选项卡三：HTML 源代码（抓取到的原始前端文件，原样展示）
        html_page = QWidget()
        html_layout = QVBoxLayout(html_page)
        html_bar = QHBoxLayout()
        self.html_meta_label = QLabel(t("html_meta_empty"))
        self.html_meta_label.setStyleSheet("color:#555;")
        self.save_html_btn = QPushButton(t("save_html_btn"))
        self.save_html_btn.clicked.connect(self._save_html_file)
        html_bar.addWidget(self.html_meta_label)
        html_bar.addStretch(1)
        html_bar.addWidget(self.save_html_btn)
        html_layout.addLayout(html_bar)

        self.html_view = QTextEdit()
        self.html_view.setReadOnly(True)
        # 等宽字体显示代码，不自动换行，保留网页源码原本的排版结构
        self.html_view.setFont(QFont("Consolas", 10))
        self.html_view.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        html_layout.addWidget(self.html_view)
        self.html_tab = right.addTab(html_page, t("tab_html"))
        self.right_tabs = right

        # 缓存当前抓到的原始 HTML 与网址，供“另存为”使用
        self.current_html = ""
        self.current_url = ""

        splitter.addWidget(right)
        splitter.setSizes([760, 520])
        root_layout.addWidget(splitter, 1)

        # ---- 底部状态栏 ----
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(t("status_ready"))

    # ------------------------------------------------------------------
    # 2) 信号与槽连接
    # ------------------------------------------------------------------
    def _connect_signals(self):
        self.start_btn.clicked.connect(self.start_crawl)
        self.stop_btn.clicked.connect(self.stop_crawl)

    # ------------------------------------------------------------------
    # 2.1) 语言切换：切换后重新刷新整窗静态文案
    # ------------------------------------------------------------------
    def _on_language_changed(self, index: int):
        code = self.lang_combo.itemData(index)
        set_language(code)
        self._retranslate_ui()

    def _retranslate_ui(self):
        """把所有写在界面上的静态文字，按当前语言重新设置一遍。

        说明：已经抓到的网页标题、正文、源码是网站原始内容，不做翻译；
        这里只刷新程序自己的按钮、标签、选项卡等外壳文字。
        """
        self.setWindowTitle(t("app_title"))
        self.url_label.setText(t("url_label"))
        self.url_edit.setPlaceholderText(t("url_placeholder"))
        self.start_btn.setText(t("start_btn"))
        self.stop_btn.setText(t("stop_btn"))
        self.robot_lock_label.setText(t("robots_lock"))
        self.cf_check.setText(t("cf_check"))
        self.cf_check.setToolTip(t("cf_tooltip"))
        self.language_label.setText(t("language_label"))
        self.body_summary_label.setText(t("body_summary_label"))
        self.save_html_btn.setText(t("save_html_btn"))
        self.right_tabs.setTabText(0, t("tab_info"))
        self.right_tabs.setTabText(1, t("tab_links"))
        self.right_tabs.setTabText(2, t("tab_html"))
        # 没有抓到源码时，源码面板顶部显示空状态提示
        if not self.current_html:
            self.html_meta_label.setText(t("html_meta_empty"))
        self.status_bar.showMessage(t("status_ready"))

    # ------------------------------------------------------------------
    # 3) 开始抓取
    # ------------------------------------------------------------------
    def start_crawl(self):
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, t("warn_no_url_title"), t("warn_no_url"))
            return
        if self.worker and self.worker.isRunning():
            return

        # 切换为“抓取中”状态
        self._set_busy(True)
        self.link_list.clear()
        self.body_edit.clear()
        self.html_view.clear()
        self.current_html = ""
        self.html_meta_label.setText(t("html_meta_empty"))
        self.title_label.setText(t("status_busy_title"))
        self.robot_label.setText("")
        self.captcha_label.setText("")
        self.desc_label.setText("")

        # 启动后台线程（robots.txt 为强制检查，无需也不提供开关参数）
        self.worker = SpiderWorker(
            url=url,
            use_cloudscraper=self.cf_check.isChecked(),
        )
        self.worker.status_changed.connect(self.status_bar.showMessage)
        self.worker.robots_checked.connect(self._on_robots_result)
        self.worker.page_finished.connect(self._on_page_finished)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.finished.connect(self._on_thread_done)
        self.worker.start()

    def stop_crawl(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.status_bar.showMessage(t("status_stopping"))

    # ------------------------------------------------------------------
    # 4) 后台线程回传结果的处理函数
    # ------------------------------------------------------------------
    def _on_robots_result(self, allowed: bool, note: str):
        self.robot_label.setText(t("robots_prefix", note=note))
        if not allowed:
            self.robot_label.setStyleSheet("color: #b3261e;")
        else:
            self.robot_label.setStyleSheet("color: #2c6e2c;")

    def _on_page_finished(self, data: dict):
        # 填充右侧信息
        self.title_label.setText(t("title_prefix", title=data["title"]))
        if data["description"]:
            self.desc_label.setText(t("desc_prefix", desc=data["description"]))
        else:
            self.desc_label.setText(t("no_description"))
        self.body_edit.setPlainText(data["summary"] or t("no_body"))

        # 人机验证识别结果：只列出检测到的类型并给出合规提示，不做任何绕过
        captcha_types = data.get("captcha", [])
        if captcha_types:
            names = [
                t(CAPTCHA_I18N_KEY[k])
                for k in captcha_types
                if k in CAPTCHA_I18N_KEY
            ]
            self.captcha_label.setText(
                t("captcha_section_label") + " " + "、".join(names)
                + "\n" + t("captcha_warning")
            )
            self.captcha_label.setStyleSheet("color:#b26a00;")
        else:
            self.captcha_label.setText(
                t("captcha_section_label") + " " + t("captcha_none")
            )
            self.captcha_label.setStyleSheet("color:#2c6e2c;")

        # 填充 HTML 源代码面板：原样显示抓到的前端 HTML 文件
        self.current_html = data["html"]
        self.current_url = data["url"]
        self.html_view.setPlainText(self.current_html)
        line_count = self.current_html.count("\n") + 1
        self.html_meta_label.setText(
            t("html_meta_filled", lines=line_count, chars=len(self.current_html))
        )

        # 填充链接列表
        for text, href in data["links"]:
            item = QListWidgetItem(f"{text}\n    {href}")
            item.setData(Qt.ItemDataRole.UserRole, href)
            self.link_list.addItem(item)

        # 左侧预览内核渲染抓到的 HTML（baseUrl 用于解析图片、样式等相对资源）
        parsed = urlparse(data["url"])
        base_url = QUrl(f"{parsed.scheme}://{parsed.netloc}")
        self.browser.setHtml(data["html"], base_url)

        self.status_bar.showMessage(
            t("status_done", url=data["url"], code=data["status_code"], n=len(data["links"]))
        )

    # ------------------------------------------------------------------
    # 把当前抓到的原始 HTML 另存为本地 .html 文件
    # ------------------------------------------------------------------
    def _save_html_file(self):
        if not self.current_html:
            QMessageBox.information(self, t("info_no_html_title"), t("info_no_html"))
            return

        # 默认文件名取域名，替换掉文件名里不允许出现的字符
        host = urlparse(self.current_url).netloc or "page"
        safe_name = "".join(ch if ch not in '\\/:*?"<>|' else "_" for ch in host)
        default_name = safe_name + ".html"

        path, _ = QFileDialog.getSaveFileName(
            self, t("save_html_btn"), default_name, t("save_dialog_filter")
        )
        if not path:
            return

        try:
            # 用 UTF-8 原样写出，换行保持 Unix 风格，不改动源码内容
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(self.current_html)
            self.status_bar.showMessage(t("save_success", path=path))
        except Exception as e:
            QMessageBox.critical(self, t("save_fail_title"), t("save_fail", err=e))

    def _on_error(self, message: str):
        self.status_bar.showMessage(t("status_error"))
        self.title_label.setText(t("crawl_fail_title"))
        QMessageBox.critical(self, t("crawl_fail_title"), message)

    def _on_thread_done(self):
        self._set_busy(False)
        self.worker = None

    # ------------------------------------------------------------------
    # 5) 双击链接：重新抓取该链接
    # ------------------------------------------------------------------
    def _open_link(self, item: QListWidgetItem):
        href = item.data(Qt.ItemDataRole.UserRole)
        if href:
            self.url_edit.setText(href)
            self.start_crawl()

    # ------------------------------------------------------------------
    # 小工具：切换按钮可用状态
    # ------------------------------------------------------------------
    def _set_busy(self, busy: bool):
        self.start_btn.setEnabled(not busy)
        self.stop_btn.setEnabled(busy)
        self.url_edit.setEnabled(not busy)


def main():
    # 必须在创建 QApplication 之前设置：把内置 Chromium 内核的日志级别压到最高，
    # 只保留致命错误，屏蔽 10108、iCCP、JS 特性不识别等无害警告（不影响任何功能）。
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--log-level=3")

    app = QApplication(sys.argv)
    # 全局默认字体（中文显示更清晰）
    app.setFont(QFont("Microsoft YaHei", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
