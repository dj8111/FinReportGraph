"""
投顧報告 PDF 轉 Markdown 圖形化一鍵轉換工具 (GUI Converter)
基於 PySide6 開發，支援資料夾瀏覽、後台非同步轉換、即時進度條與日誌輸出。
"""

import sys
import os
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QProgressBar, QTextEdit,
    QFileDialog, QCheckBox, QFrame, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QIcon

# 匯入核心轉換引擎
from converter_core import convert_all_in_folder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class ConversionWorker(QThread):
    progress_signal = Signal(int, int, str)
    log_signal = Signal(str, str)
    finished_signal = Signal(list)
    error_signal = Signal(str)

    def __init__(self, input_dir, output_dir):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir

    def run(self):
        try:
            def on_progress(current, total, filename):
                self.progress_signal.emit(current, total, filename)

            def on_log(message, level):
                self.log_signal.emit(message, level)

            results = convert_all_in_folder(
                self.input_dir,
                self.output_dir,
                progress_callback=on_progress,
                log_callback=on_log
            )
            self.finished_signal.emit(results)
        except Exception as e:
            self.error_signal.emit(str(e))

class ModernConverterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 轉 Markdown 投顧報告智能轉換器")
        self.resize(880, 720)
        self.setMinimumSize(780, 600)
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # 1. 標題與簡介橫幅
        header_layout = QVBoxLayout()
        header_title = QLabel("📑 投顧報告 PDF 轉 Markdown 智能轉換工具")
        header_title.setFont(QFont("Microsoft JhengHei UI", 16, QFont.Bold))
        header_title.setStyleSheet("color: #38bdf8;")
        
        header_desc = QLabel("支援自動字元碼逆向修復（防亂碼）、去除免責聲明雜訊、提取 30 字以內摘要，一鍵批次產出排版工整之 Markdown。")
        header_desc.setFont(QFont("Microsoft JhengHei UI", 9))
        header_desc.setStyleSheet("color: #94a3b8;")
        header_desc.setWordWrap(True)
        
        header_layout.addWidget(header_title)
        header_layout.addWidget(header_desc)
        main_layout.addLayout(header_layout)

        # 2. 資料夾選擇面板
        path_group = QGroupBox("📁 檔案目錄設定")
        path_layout = QVBoxLayout(path_group)
        path_layout.setSpacing(12)

        # Input Row
        in_row = QHBoxLayout()
        in_label = QLabel("PDF 輸入資料夾:")
        in_label.setFixedWidth(120)
        self.in_edit = QLineEdit()
        self.in_edit.setText(os.path.join(BASE_DIR, "raw"))
        self.in_edit.setPlaceholderText("請選擇存放 PDF 報告的資料夾...")
        
        in_browse_btn = QPushButton("瀏覽...")
        in_browse_btn.clicked.connect(self.browse_input_dir)
        in_open_btn = QPushButton("開啟")
        in_open_btn.clicked.connect(lambda: self.open_in_explorer(self.in_edit.text()))
        
        in_row.addWidget(in_label)
        in_row.addWidget(self.in_edit)
        in_row.addWidget(in_browse_btn)
        in_row.addWidget(in_open_btn)
        path_layout.addLayout(in_row)

        # Output Row
        out_row = QHBoxLayout()
        out_label = QLabel("Markdown 輸出:")
        out_label.setFixedWidth(120)
        self.out_edit = QLineEdit()
        self.out_edit.setText(os.path.join(BASE_DIR, "markdown"))
        self.out_edit.setPlaceholderText("請選擇輸出 Markdown 檔案的目標資料夾...")
        
        out_browse_btn = QPushButton("瀏覽...")
        out_browse_btn.clicked.connect(self.browse_output_dir)
        out_open_btn = QPushButton("開啟")
        out_open_btn.clicked.connect(lambda: self.open_in_explorer(self.out_edit.text()))
        
        out_row.addWidget(out_label)
        out_row.addWidget(self.out_edit)
        out_row.addWidget(out_browse_btn)
        out_row.addWidget(out_open_btn)
        path_layout.addLayout(out_row)

        main_layout.addWidget(path_group)

        # 3. 轉換選項
        opt_layout = QHBoxLayout()
        self.chk_fix_font = QCheckBox("啟用特殊字型逆向修復 (Identity-H 解碼)")
        self.chk_fix_font.setChecked(True)
        self.chk_clean = QCheckBox("去除頁尾免責聲明與頁碼雜訊")
        self.chk_clean.setChecked(True)
        self.chk_summary = QCheckBox("提煉 30 字精準摘要與 YAML 標籤")
        self.chk_summary.setChecked(True)
        
        opt_layout.addWidget(self.chk_fix_font)
        opt_layout.addWidget(self.chk_clean)
        opt_layout.addWidget(self.chk_summary)
        main_layout.addLayout(opt_layout)

        # 4. 核心執行按鈕
        self.convert_btn = QPushButton("🚀 一鍵轉換成 Markdown")
        self.convert_btn.setFixedHeight(46)
        self.convert_btn.setFont(QFont("Microsoft JhengHei UI", 12, QFont.Bold))
        self.convert_btn.clicked.connect(self.start_conversion)
        main_layout.addWidget(self.convert_btn)

        # 5. 進度條與狀態提示
        progress_layout = QVBoxLayout()
        self.status_label = QLabel("💡 點擊「一鍵轉換成 Markdown」即可自動批次處理指定資料夾中的所有 PDF 檔案。")
        self.status_label.setStyleSheet("color: #cbd5e1; font-size: 13px;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setTextVisible(True)
        
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(self.progress_bar)
        main_layout.addLayout(progress_layout)

        # 6. 即時日誌視窗
        log_group = QGroupBox("📋 轉換即時日誌")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_group)

        # 7. 底部快捷操作按鈕
        bottom_layout = QHBoxLayout()
        self.btn_open_output = QPushButton("📂 開啟輸出資料夾")
        self.btn_open_output.clicked.connect(lambda: self.open_in_explorer(self.out_edit.text()))
        
        self.btn_open_graph = QPushButton("🌐 開啟互動式知識圖譜 (HTML)")
        self.btn_open_graph.clicked.connect(self.open_knowledge_graph)
        
        self.btn_clear_log = QPushButton("🧹 清除日誌")
        self.btn_clear_log.clicked.connect(self.log_text.clear)
        
        bottom_layout.addWidget(self.btn_open_output)
        bottom_layout.addWidget(self.btn_open_graph)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_clear_log)
        main_layout.addLayout(bottom_layout)

    def apply_styles(self):
        """專業深色現代化主題樣式 (Dark Slate Modern Theme)"""
        qss = """
        QMainWindow {
            background-color: #0f172a;
        }
        QWidget {
            color: #f1f5f9;
            font-family: "Microsoft JhengHei UI", Segoe UI, sans-serif;
        }
        QGroupBox {
            font-weight: bold;
            font-size: 13px;
            color: #38bdf8;
            border: 1px solid #334155;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 14px;
            background-color: #1e293b;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 14px;
            padding: 0 6px;
        }
        QLineEdit {
            background-color: #0f172a;
            border: 1px solid #475569;
            border-radius: 6px;
            padding: 6px 12px;
            color: #f8fafc;
            font-size: 12px;
        }
        QLineEdit:focus {
            border: 1px solid #38bdf8;
        }
        QPushButton {
            background-color: #334155;
            color: #f8fafc;
            border: 1px solid #475569;
            border-radius: 6px;
            padding: 6px 14px;
            font-weight: 600;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #475569;
            border-color: #64748b;
        }
        QPushButton:pressed {
            background-color: #1e293b;
        }
        QPushButton#convert_btn, QPushButton:default {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #2563eb);
            color: #ffffff;
            border: none;
            border-radius: 8px;
        }
        QPushButton#convert_btn:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:1 #1d4ed8);
        }
        QProgressBar {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            text-align: center;
            color: #ffffff;
            font-weight: bold;
            font-size: 11px;
        }
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #10b981);
            border-radius: 7px;
        }
        QTextEdit {
            background-color: #0b1120;
            border: 1px solid #1e293b;
            border-radius: 6px;
            color: #cbd5e1;
            font-family: Consolas, "Courier New", monospace;
            font-size: 12px;
            padding: 8px;
        }
        QCheckBox {
            color: #cbd5e1;
            font-size: 12px;
            spacing: 6px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border-radius: 4px;
            border: 1px solid #475569;
            background: #0f172a;
        }
        QCheckBox::indicator:checked {
            background: #0284c7;
            border-color: #38bdf8;
        }
        """
        self.setStyleSheet(qss)
        self.convert_btn.setObjectName("convert_btn")

    def browse_input_dir(self):
        curr = self.in_edit.text() if os.path.exists(self.in_edit.text()) else ""
        d = QFileDialog.getExistingDirectory(self, "選擇 PDF 輸入資料夾", curr)
        if d:
            self.in_edit.setText(os.path.normpath(d))

    def browse_output_dir(self):
        curr = self.out_edit.text() if os.path.exists(self.out_edit.text()) else ""
        d = QFileDialog.getExistingDirectory(self, "選擇 Markdown 輸出資料夾", curr)
        if d:
            self.out_edit.setText(os.path.normpath(d))

    def open_in_explorer(self, path):
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "提示", f"路徑不存在: {path}")
            return
        os.startfile(os.path.normpath(path))

    def open_knowledge_graph(self):
        html_path = os.path.join(BASE_DIR, "graph", "knowledge_graph.html")
        if os.path.exists(html_path):
            os.startfile(html_path)
        else:
            QMessageBox.information(self, "提示", "尚未找到 knowledge_graph.html，請先確認專案目錄。")

    def append_log(self, msg, level="info"):
        colors = {
            "info": "#94a3b8",
            "success": "#4ade80",
            "error": "#f87171",
            "warning": "#fbbf24",
            "done": "#38bdf8"
        }
        color = colors.get(level, "#cbd5e1")
        prefix = {
            "info": "ℹ️ ",
            "success": "✅ ",
            "error": "❌ ",
            "warning": "⚠️ ",
            "done": "🎉 "
        }.get(level, "")
        html = f"<div style='color: {color}; margin: 2px 0;'>{prefix}{msg}</div>"
        self.log_text.append(html)

    def start_conversion(self):
        input_dir = self.in_edit.text().strip()
        output_dir = self.out_edit.text().strip()

        if not os.path.exists(input_dir):
            QMessageBox.critical(self, "錯誤", f"輸入資料夾不存在：\n{input_dir}")
            return

        # Disable button during conversion
        self.convert_btn.setEnabled(False)
        self.convert_btn.setText("⏳ 正在轉換中，請稍候...")
        self.progress_bar.setValue(0)
        self.append_log(f"開始掃描資料夾: {input_dir}", "info")

        # Launch Worker Thread
        self.worker = ConversionWorker(input_dir, output_dir)
        self.worker.progress_signal.connect(self.on_progress)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(self.on_error)
        self.worker.start()

    def on_progress(self, current, total, filename):
        pct = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(pct)
        self.status_label.setText(f"處理進度: [{current}/{total}] {filename}")

    def on_finished(self, results):
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("🚀 一鍵轉換成 Markdown")
        self.status_label.setText(f"🎉 轉換圓滿完成！共成功轉換 {len(results)} 份報告。")
        QMessageBox.information(
            self,
            "轉換完成",
            f"恭喜！已成功將 {len(results)} 份 PDF 報告完整轉換為 Markdown！\n\n"
            f"輸出資料夾：\n{self.out_edit.text()}\n\n"
            "已自動同步提煉 30 字精準摘要並生成目錄彙整表。"
        )

    def on_error(self, err_msg):
        self.convert_btn.setEnabled(True)
        self.convert_btn.setText("🚀 一鍵轉換成 Markdown")
        self.append_log(f"發生未預期錯誤: {err_msg}", "error")
        QMessageBox.critical(self, "轉換失敗", f"執行過程中發生錯誤：\n{err_msg}")

def main():
    app = QApplication(sys.argv)
    window = ModernConverterWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()

