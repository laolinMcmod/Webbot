# -*- coding: utf-8 -*-
"""界面冒烟测试：只构造窗口、不联网，验证模块、控件与语言切换能正常初始化。"""
import sys
from PyQt6.QtWidgets import QApplication
from main import MainWindow
from i18n import t, LANGUAGES, set_language

app = QApplication(sys.argv)
w = MainWindow()
w.show()
app.processEvents()

assert w.url_edit is not None, "地址框缺失"
assert w.browser is not None, "预览内核缺失"
assert w.start_btn is not None
assert w.robot_lock_label is not None, "强制遵守 robots 提示标签缺失"
assert w.html_view is not None, "HTML 源代码面板缺失"
assert w.save_html_btn is not None, "另存为按钮缺失"
assert w.lang_combo is not None, "语言切换下拉框缺失"
assert w.captcha_label is not None, "人机验证提示标签缺失"
# 下拉框条目数必须和语言包登记的数量一致
assert w.lang_combo.count() == len(LANGUAGES), "语言下拉框条目数与语言表不一致"

# ---- 语言切换自检：切到英文，再切回中文，检查按钮文字跟着变 ----
w.lang_combo.setCurrentIndex(1)  # 第二项是 English
app.processEvents()
assert w.start_btn.text() == t("start_btn"), "切换英文后“开始”按钮文字未刷新"
w.lang_combo.setCurrentIndex(0)  # 切回简体中文
app.processEvents()
assert w.start_btn.text() == t("start_btn"), "切回中文后按钮文字未刷新"
set_language("zh")

print("窗口标题:", w.windowTitle())
print("控件构造正常：地址框 / 浏览器内核 / 按钮 / robots 提示 / 源码面板 / 语言框 均已创建")
print("语言切换正常：简体中文 ⇄ English 文案刷新成功")
print("SMOKE OK")
w.close()
